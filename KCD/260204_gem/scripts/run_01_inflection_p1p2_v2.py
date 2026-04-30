"""
변곡점 추출 및 P1/P2 라벨링 (Optimized & Visualized & Robust)
- Numpy Vectorization을 통한 속도 최적화
- SVD 에러 방지 (NaN 처리 및 예외 처리 추가)
"""
from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import warnings

# 경고 무시 (RuntimeWarning: invalid value encountered in divide 등)
warnings.filterwarnings('ignore')

# 한글 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "outputs" / "logs" / "run_01_inflection_p1p2.log"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"

DEFAULT_HALF_WEEKS = 71

def log(msg: str):
    line = f"{datetime.now().isoformat()} {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    # print(msg) # 진행바(tqdm) 깨짐 방지를 위해 print 주석 처리 가능

def get_weekly_path():
    primary = ROOT.parent / "original_data" / "weekly_processed.parquet"
    if primary.exists(): return primary
    return ROOT.parent / "original_data" / "weekly.parquet"

# =============================================================================
# [Core Logic] O(N) 최적화된 변곡점 탐색 (Robust Version)
# =============================================================================
def find_best_inflection_fast(y_values, min_segment=4, default_break=71):
    """
    Numpy 누적합을 이용하여 RSS를 계산. 에러 발생 시 Fallback 처리.
    """
    # 1. NaN / Inf 처리 (중요: 에러 원인 차단)
    y_values = np.nan_to_num(y_values, nan=0.0, posinf=0.0, neginf=0.0)
    
    n = len(y_values)
    
    # 데이터가 너무 짧거나, 모든 값이 0인 경우 Fallback
    if n < 2 * min_segment or np.all(y_values == 0):
        try:
            x = np.arange(n)
            # 데이터가 0이거나 너무 작으면 기울기 0
            if np.all(y_values == 0) or len(y_values) < 2:
                 return (n // 2), 0.0, 0.0, True
            
            slope, intercept = np.polyfit(x, y_values, 1)
            return (n // 2), slope, slope, True
        except Exception:
            # 그래도 에러나면 0 리턴
            return (n // 2), 0.0, 0.0, True

    x = np.arange(n)
    
    # 누적합(Prefix Sum) 계산
    s_x = np.cumsum(x)
    s_y = np.cumsum(y_values)
    s_xx = np.cumsum(x**2)
    s_xy = np.cumsum(x*y_values)
    s_yy = np.cumsum(y_values**2)
    
    s_x = np.insert(s_x, 0, 0)
    s_y = np.insert(s_y, 0, 0)
    s_xx = np.insert(s_xx, 0, 0)
    s_xy = np.insert(s_xy, 0, 0)
    s_yy = np.insert(s_yy, 0, 0)

    def get_slope_rss(start, end):
        count = end - start
        if count < 2: return 0.0, np.inf 
        
        sum_x = s_x[end] - s_x[start]
        sum_y = s_y[end] - s_y[start]
        sum_xx = s_xx[end] - s_xx[start]
        sum_xy = s_xy[end] - s_xy[start]
        sum_yy = s_yy[end] - s_yy[start]
        
        denom = count * sum_xx - sum_x**2
        if denom == 0: return 0.0, np.inf
        
        slope = (count * sum_xy - sum_x * sum_y) / denom
        intercept = (sum_y - slope * sum_x) / count
        rss = sum_yy - intercept * sum_y - slope * sum_xy
        return slope, rss

    best_rss = np.inf
    best_k = default_break
    best_slopes = (0.0, 0.0)
    used_fallback = True

    start_k = min_segment
    end_k = n - min_segment
    search_range = range(start_k, end_k)
    
    if len(search_range) > 0:
        for k in search_range:
            try:
                s1, rss1 = get_slope_rss(0, k)
                s2, rss2 = get_slope_rss(k, n)
                
                total_rss = rss1 + rss2
                if total_rss < best_rss:
                    best_rss = total_rss
                    best_k = k
                    best_slopes = (s1, s2)
                    used_fallback = False
            except:
                continue # 계산 에러나면 해당 k 건너뜀
    
    # Fallback 로직 (탐색 실패 시)
    if used_fallback:
        try:
            s1, _ = get_slope_rss(0, min(n, default_break))
            s2, _ = get_slope_rss(min(n, default_break), n)
            # 만약 여기서도 inf가 나오면 0으로 대체
            if s1 == np.inf: s1 = 0.0
            if s2 == np.inf: s2 = 0.0
            best_slopes = (s1, s2)
        except:
            best_slopes = (0.0, 0.0)

    return best_k, best_slopes[0], best_slopes[1], used_fallback

# =============================================================================
# [Visualization] 검증용 플롯
# =============================================================================
def plot_inflection_example(weeks, sales, inflection_week, public_id, p1_label, p2_label):
    try:
        plt.figure(figsize=(10, 5))
        plt.plot(weeks, sales, label='Weekly Sales', color='lightgray', marker='.', alpha=0.6)
        
        mask1 = weeks < inflection_week
        if mask1.sum() > 1:
            z1 = np.polyfit(weeks[mask1], sales[mask1], 1)
            p1_line = np.poly1d(z1)
            plt.plot(weeks[mask1], p1_line(weeks[mask1]), 'r-', lw=2, label=f'P1 ({p1_label})')

        mask2 = weeks >= inflection_week
        if mask2.sum() > 1:
            z2 = np.polyfit(weeks[mask2], sales[mask2], 1)
            p2_line = np.poly1d(z2)
            plt.plot(weeks[mask2], p2_line(weeks[mask2]), 'b-', lw=2, label=f'P2 ({p2_label})')

        plt.axvline(x=inflection_week, color='green', linestyle='--', label='Inflection Point')
        plt.title(f"Store {public_id}: {p1_label} -> {p2_label} (Week {inflection_week})")
        plt.legend()
        plt.tight_layout()
        
        save_path = FIGURES_DIR / f"inflection_{public_id}.png"
        plt.savefig(save_path)
        plt.close()
    except Exception as e:
        log(f"Plot Error for {public_id}: {e}")

def main(limit_stores=None):
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    weekly_path = get_weekly_path()
    log(f"Loading data from {weekly_path}...")
    
    cols = ['public_id', 'date_id', 'sales_card'] 
    df = pd.read_parquet(weekly_path, columns=cols)
    
    dates = sorted(df['date_id'].unique())
    date_map = {d: i for i, d in enumerate(dates)}
    df['week_idx'] = df['date_id'].map(date_map)
    
    if limit_stores:
        target_ids = df['public_id'].unique()[:limit_stores]
        df = df[df['public_id'].isin(target_ids)]
    
    log(f"Data Loaded: {len(df)} rows, {df['public_id'].nunique()} stores.")

    results = []
    plot_count = 0
    
    grouped = df.groupby('public_id')
    
    log("Starting inflection point search...")
    
    # tqdm 사용 시 에러나면 바로 볼 수 있게 설정
    for pid, group in tqdm(grouped, total=len(grouped)):
        group = group.sort_values('week_idx')
        y = group['sales_card'].values
        
        # [핵심 수정] NaN 처리 및 에러 핸들링
        y = np.nan_to_num(y, nan=0.0) 
        
        try:
            k, s1, s2, fallback = find_best_inflection_fast(y, min_segment=4, default_break=DEFAULT_HALF_WEEKS)
        except Exception as e:
            # 치명적 에러 발생 시 해당 업장 스킵하고 계속 진행
            # log(f"Skipping store {pid} due to error: {e}")
            continue
        
        p1_lbl = 'U' if s1 > 0 else 'D'
        p2_lbl = 'U' if s2 > 0 else 'D'
        
        results.append({
            'public_id': pid,
            'inflection_week': k,
            'P1_label': p1_lbl,
            'P2_label': p2_lbl,
            'P1_slope': s1,
            'P2_slope': s2,
            'used_fallback': fallback
        })

        if plot_count < 10 and not fallback:
            try:
                weeks = np.arange(len(y))
                plot_inflection_example(weeks, y, k, pid, p1_lbl, p2_lbl)
                plot_count += 1
            except:
                pass

    out_df = pd.DataFrame(results)
    out_path = TABLES_DIR / "inflection_p1p2_labels.csv"
    out_df.to_csv(out_path, index=False)
    
    log(f"Analysis Complete. Results saved to {out_path}")
    print(out_df.groupby(['P1_label', 'P2_label']).size())

if __name__ == "__main__":
    main(limit_stores=None)
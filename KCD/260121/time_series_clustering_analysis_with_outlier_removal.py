"""
시계열 클러스터링 및 분포 분석 스크립트 (이상치 제거 버전)
- 각 업장의 시계열에서 이상치 제거
- 이상치가 많은 업장 제거
- KCD_timeSeries_Clustering.ipynb와 동일한 작업 수행
weekly_processed.parquet 사용
"""

# 패키지 불러오기
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# tslearn import 체크
try:
    from tslearn.clustering import TimeSeriesKMeans
except ImportError:
    print("ERROR: tslearn 패키지가 설치되지 않았습니다.")
    print("다음 명령어로 설치해주세요: pip install tslearn")
    raise

# 한글 폰트 설정 (macOS)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("시계열 클러스터링 및 분포 분석 시작 (이상치 제거 버전)")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

# weekly_processed.parquet 사용 (이미 day_after1, sales_ratio가 계산되어 있음)
df = pd.read_parquet('/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/original_data/weekly_processed.parquet')
meta_df = pd.read_csv('/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/original_data/meta_processed.csv')

print(f"weekly_processed.parquet: {df.shape}")
print(f"meta_processed.csv: {meta_df.shape}")

# day_after1=0 제외 (기존 노트북과 동일)
df = df[~df['day_after1'].isin([0])]

print(f"day_after1=0 제외 후: {df.shape}")

# ============================================================================
# 2. 시계열 데이터 생성
# ============================================================================
print("\n[2] 시계열 데이터 생성 중...")

# id별 시리즈 생성 (노트북과 동일)
# 중복된 day_after1 값이 있을 수 있으므로 평균으로 집계
grouped = df.groupby('public_id')
series_dict = {}
for pid, group in grouped:
    # day_after1별로 평균을 계산하여 중복 제거
    series = group.groupby('day_after1')['sales_ratio'].mean()
    series_dict[pid] = series.sort_index()
mySeries = series_dict
namesofMyseries = list(mySeries.keys())

print(f"생성된 시계열 수: {len(mySeries)}")

# ============================================================================
# 3. 시계열 전처리 및 매출 이상치 업장 제거
# ============================================================================
print("\n[3] 시계열 전처리 및 매출 이상치 업장 제거 중...")

# 최소 길이 필터링 (95개 이상)
mySeries_filtered = {key: series for key, series in mySeries.items() if len(series) >= 95}
print(f"최소 길이 필터링 후 시계열 수: {len(mySeries_filtered)} (95개 이상)")

# 각 업장의 평균 매출 계산 (sales_card 기준)
print("  - 각 업장의 평균 매출 계산 중...")
store_avg_sales = []
for pid in mySeries_filtered.keys():
    store_data = df[df['public_id'] == pid]
    avg_sales = store_data['sales_card'].mean()
    total_sales = store_data['sales_card'].sum()
    store_avg_sales.append({
        'public_id': pid,
        'avg_sales_card': avg_sales,
        'total_sales_card': total_sales,
        'max_sales_card': store_data['sales_card'].max(),
        'min_sales_card': store_data['sales_card'].min()
    })

store_sales_df = pd.DataFrame(store_avg_sales)
print(f"    계산 완료: {len(store_sales_df)}개 업장")

# # 매출 이상치 업장 제거 (IQR 방법)
# print("  - 매출 이상치 업장 제거 중 (IQR 방법)...")

# # 평균 매출 기준으로 이상치 제거
# avg_sales_values = store_sales_df['avg_sales_card'].values
# Q1 = np.percentile(avg_sales_values, 25)
# Q3 = np.percentile(avg_sales_values, 75)
# IQR = Q3 - Q1
# lower_bound = Q1 - 1.5 * IQR
# upper_bound = Q3 + 1.5 * IQR

# print(f"    평균 매출 통계:")
# print(f"      Q1: {Q1:,.0f}원")
# print(f"      Q3: {Q3:,.0f}원")
# print(f"      IQR: {IQR:,.0f}원")
# print(f"      이상치 범위: {lower_bound:,.0f}원 ~ {upper_bound:,.0f}원")

# # 이상치 업장 식별
# outlier_mask = (store_sales_df['avg_sales_card'] >= lower_bound) & (store_sales_df['avg_sales_card'] <= upper_bound)
# outlier_stores = store_sales_df[~outlier_mask]
# normal_stores = store_sales_df[outlier_mask]

# print(f"\n    이상치 업장: {len(outlier_stores)}개")
# print(f"    정상 업장: {len(normal_stores)}개")
# print(f"    이상치 업장 비율: {len(outlier_stores)/len(normal_stores):.2f}")
# 매출 이상치 업장 제거 (Percentile 방법 - 제거 비율 제어)
print("  - 매출 이상치 업장 제거 중 (Percentile 방법)...")

# 제거 비율 설정 (1~5% 사이, 상하위 각각 제거)
outlier_removal_percent = 2.5  # 상위 2.5% + 하위 2.5% = 총 5% 제거
lower_percentile = outlier_removal_percent
upper_percentile = 100 - outlier_removal_percent

# 평균 매출 기준으로 이상치 제거
avg_sales_values = store_sales_df['avg_sales_card'].values
lower_bound = np.percentile(avg_sales_values, lower_percentile)
upper_bound = np.percentile(avg_sales_values, upper_percentile)

print(f"    제거 비율 설정: 상위 {outlier_removal_percent}% + 하위 {outlier_removal_percent}% = 총 {outlier_removal_percent * 2}%")
print(f"    평균 매출 통계:")
print(f"      하위 {lower_percentile}% 임계값: {lower_bound:,.0f}원")
print(f"      상위 {upper_percentile}% 임계값: {upper_bound:,.0f}원")
print(f"      전체 평균: {np.mean(avg_sales_values):,.0f}원")
print(f"      전체 중앙값: {np.median(avg_sales_values):,.0f}원")

# 이상치 업장 식별
outlier_mask = (store_sales_df['avg_sales_card'] >= lower_bound) & (store_sales_df['avg_sales_card'] <= upper_bound)
outlier_stores = store_sales_df[~outlier_mask]
normal_stores = store_sales_df[outlier_mask]

outlier_ratio = len(outlier_stores) / len(store_sales_df) * 100

print(f"\n    이상치 업장: {len(outlier_stores)}개")
print(f"    정상 업장: {len(normal_stores)}개")
print(f"    이상치 업장 비율: {outlier_ratio:.2f}%")


if len(outlier_stores) > 0:
    print(f"\n    이상치 업장 통계:")
    print(f"      평균 매출 범위: {outlier_stores['avg_sales_card'].min():,.0f}원 ~ {outlier_stores['avg_sales_card'].max():,.0f}원")
    print(f"      평균: {outlier_stores['avg_sales_card'].mean():,.0f}원")

# 정상 업장만 선택
normal_store_ids = set(normal_stores['public_id'].values)
mySeries_cleaned = {key: series for key, series in mySeries_filtered.items() if key in normal_store_ids}

print(f"\n  매출 이상치 제거 후 시계열 수: {len(mySeries_cleaned)}")
print(f"  제외된 업장 수: {len(mySeries_filtered) - len(mySeries_cleaned)}")

# 가장 긴 시계열 찾기
max_len = max(len(series) for series in mySeries_cleaned.values())
longest_series = None
for series in mySeries_cleaned.values():
    if len(series) == max_len:
        # 인덱스 중복 확인 및 제거
        if series.index.duplicated().any():
            longest_series = series.groupby(series.index).mean()
        else:
            longest_series = series
        break

print(f"가장 긴 시계열 길이: {max_len}")
print(f"longest_series 인덱스 중복 여부: {longest_series.index.duplicated().any()}")

# 길이 통일 (reindex)
mySeries_aligned = {}
problems_index = []
for i, (key, series) in enumerate(mySeries_cleaned.items()):
    # 인덱스 중복 확인 및 제거
    if series.index.duplicated().any():
        series = series.groupby(series.index).mean()
    
    if len(series) != max_len:
        problems_index.append(i)
        # longest_series.index가 고유한지 확인
        if longest_series.index.duplicated().any():
            longest_index = longest_series.index.drop_duplicates()
        else:
            longest_index = longest_series.index
        aligned_series = series.reindex(longest_index)
        mySeries_aligned[key] = aligned_series
    else:
        mySeries_aligned[key] = series

print(f"길이 통일 완료: 모든 시계열 길이 = {max_len}")

# 날짜 채우기로 인한 NA값 가장 가까운 매출값으로 채우기 (노트북과 동일)
for key in mySeries_aligned:
    if mySeries_aligned[key].isnull().sum() > 0:
        mySeries_aligned[key].interpolate(limit_direction="both", inplace=True)

# NaN 체크
nan_count = sum(1 for series in mySeries_aligned.values() if series.isnull().sum() > 0)
print(f"보간 후 NaN이 있는 시계열 수: {nan_count}")

# MinMaxScaler로 정규화 (0-1 범위)
mySeries_normalized = {}
for key, series in mySeries_aligned.items():
    scaler = MinMaxScaler()
    data_reshaped = np.array(series).reshape(-1, 1)
    normalized = scaler.fit_transform(data_reshaped)
    mySeries_normalized[key] = normalized.reshape(-1)

print(f"정규화 완료: {len(mySeries_normalized)}개 시계열")

# tslearn 형식으로 변환 (numpy array 리스트)
mySeries_list = list(mySeries_normalized.values())
public_ids_list = list(mySeries_normalized.keys())

# tslearn은 (n_ts, sz, d) 형태의 배열을 요구
X = np.array([series.reshape(-1, 1) for series in mySeries_list])
print(f"클러스터링용 데이터 형태: {X.shape}")

# ============================================================================
# 4. 클러스터링 수행
# ============================================================================
print("\n[4] 클러스터링 수행 중...")

# TimeSeriesKMeans 사용 (n_clusters=9, metric="euclidean")
km = TimeSeriesKMeans(n_clusters=9, metric="euclidean", random_state=42, verbose=True)
labels = km.fit_predict(X)

print(f"클러스터링 완료: {len(labels)}개 시계열, {len(set(labels))}개 클러스터")

# 클러스터별 개수
cluster_counts = pd.Series(labels).value_counts().sort_index()
print("\n클러스터별 개수:")
print(cluster_counts)

# public_id와 클러스터 라벨 매핑
cluster_mapping = pd.DataFrame({
    'public_id': public_ids_list,
    'cluster': labels
})

# 클러스터별 분류 코드 매핑
cluster_code_mapping = {
    0: 'DDY',  # 뚜렷한 변곡점 없이 서서히 낮아져 낮은 수치에서 유지됨 (안정)
    1: 'DUY',  # 50주차 하락 후 다시 반등하여 초기 수준과 비슷하게 유지 (안정)
    2: 'UDX',  # 70주차까지 급등 후 미세하게 하락하나, 전체적으론 크게 상승 (성장)
    3: 'DDZ',  # 지속적인 하락 곡선을 그리며 수치가 계속 낮아짐 (퇴로)
    4: 'UUX',  # 변곡점 없이 꾸준히 상승하여 높은 수치로 마감 (성장)
    5: 'DUX',  # 50주차 급락 후 다시 강하게 반등하여 시작점보다 높게 마감 (성장)
    6: 'DDZ',  # 변곡점 이후에도 하락세가 멈추지 않고 최하단으로 수렴 (퇴로)
    7: 'DDY',  # 전체 기간 동안 큰 변화 없이 0.3 부근에서 횡보 (안정)
    8: 'DDY'   # 높은 구간(0.6)에서 시작해 미세하게 낮아지나 일정 수준 유지 (안정)
}

# 클러스터 코드 컬럼 추가
cluster_mapping['label'] = cluster_mapping['cluster'].map(cluster_code_mapping)

# ============================================================================
# 5. 클러스터 시각화 (노트북과 동일한 스타일)
# ============================================================================
print("\n[5] 클러스터 시각화 중...")

# 결과 저장 디렉토리
result_img_dir = '/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260121/result_img'
result_csv_dir = '/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260121/result_csv'
os.makedirs(result_img_dir, exist_ok=True)
os.makedirs(result_csv_dir, exist_ok=True)

# 클러스터별 시계열 그래프 (노트북과 동일한 스타일)
plot_count = 9
fig, axs = plt.subplots(3, 3, figsize=(25, 25))

rows = 3
columns = 3

row_i = 0
column_j = 0

for label in sorted(set(labels)):
    cluster = []
    for i in range(len(labels)):
        if labels[i] == label:
            axs[row_i, column_j].plot(mySeries_list[i], c="gray", alpha=0.4)
            cluster.append(mySeries_list[i])
    
    # 클러스터 평균선 그리기
    if len(cluster) > 0:
        axs[row_i, column_j].plot(np.average(np.vstack(cluster), axis=0), c="red", linewidth=2)
    
    axs[row_i, column_j].set_title("Cluster " + str(label) + " (Outlier Removed)", fontsize=30)
    axs[row_i, column_j].set_xlabel('Week', fontsize=15)
    axs[row_i, column_j].set_ylabel('Normalized Sales Ratio', fontsize=15)
    axs[row_i, column_j].grid(True, alpha=0.3)
    
    # Update column and row indices
    column_j += 1
    if column_j >= columns:
        row_i += 1
        column_j = 0

plt.tight_layout()
plt.savefig(os.path.join(result_img_dir, 'cluster_timeseries_with_outlier_removal.png'), dpi=300, bbox_inches='tight')
print("클러스터별 시계열 그래프 저장: cluster_timeseries_with_outlier_removal.png")

# 클러스터별 개수 분포 그래프 (노트북과 동일하게 가로 막대)
plt.figure(figsize=(12, 8))
cluster_c = [len(labels[labels == i]) for i in range(9)]
cluster_n = ["Cluster " + str(i) for i in range(9)]

# 노트북과 동일하게 역순으로 (barh는 아래에서 위로 표시되므로)
cluster_c = cluster_c[::-1]
cluster_n = cluster_n[::-1]

plt.barh(cluster_n, cluster_c, color='steelblue')
plt.title('클러스터별 개수 분포 (이상치 제거)', fontsize=20)
plt.xlabel('Count', fontsize=15)
plt.ylabel('Cluster', fontsize=15)
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig(os.path.join(result_img_dir, 'cluster_distribution_with_outlier_removal.png'), dpi=300, bbox_inches='tight')
print("클러스터별 개수 분포 그래프 저장: cluster_distribution_with_outlier_removal.png")

# ============================================================================
# 6. 클러스터별 업장 분포 분석
# ============================================================================
print("\n[6] 클러스터별 업장 분포 분석 중...")

# 메타데이터와 클러스터 매핑 결합
analysis_df = cluster_mapping.merge(meta_df, on='public_id', how='left')

# depth 컬럼명 (meta_processed.csv는 이미 간소화됨)
depth_1_col = 'depth_1'
depth_2_col = 'depth_2'
depth_3_col = 'depth_3'

# 각 카테고리별로 별도로 저장
depth_1_results = []
depth_2_results = []
depth_3_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    total_in_cluster = len(cluster_data)
    
    if total_in_cluster == 0:
        continue
    
    # depth_1별 분포
    depth_1_dist = cluster_data[depth_1_col].value_counts()
    for depth_1, count in depth_1_dist.items():
        depth_1_results.append({
            'cluster': cluster_id,
            'depth_1': depth_1,
            'count': count,
            'ratio': count / total_in_cluster
        })
    
    # depth_2별 분포
    depth_2_dist = cluster_data[depth_2_col].value_counts()
    for depth_2, count in depth_2_dist.items():
        depth_2_results.append({
            'cluster': cluster_id,
            'depth_2': depth_2,
            'count': count,
            'ratio': count / total_in_cluster
        })
    
    # depth_3별 분포
    depth_3_dist = cluster_data[depth_3_col].value_counts()
    for depth_3, count in depth_3_dist.items():
        depth_3_results.append({
            'cluster': cluster_id,
            'depth_3': depth_3,
            'count': count,
            'ratio': count / total_in_cluster
        })

depth_1_df = pd.DataFrame(depth_1_results)
depth_2_df = pd.DataFrame(depth_2_results)
depth_3_df = pd.DataFrame(depth_3_results)

print(f"업장 분포 분석 완료:")
print(f"  - depth_1: {len(depth_1_df)}개 레코드")
print(f"  - depth_2: {len(depth_2_df)}개 레코드")
print(f"  - depth_3: {len(depth_3_df)}개 레코드")

# ============================================================================
# 7. 클러스터별 지역 분포 분석
# ============================================================================
print("\n[7] 클러스터별 지역 분포 분석 중...")

# 각 지역별로 별도로 저장
sigungu_results = []
dong_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    total_in_cluster = len(cluster_data)
    
    if total_in_cluster == 0:
        continue
    
    # sigungu별 분포
    sigungu_dist = cluster_data['sigungu'].value_counts()
    for sigungu, count in sigungu_dist.items():
        sigungu_results.append({
            'cluster': cluster_id,
            'sigungu': sigungu,
            'count': count,
            'ratio': count / total_in_cluster
        })
    
    # dong별 분포
    dong_dist = cluster_data['dong'].value_counts()
    for dong, count in dong_dist.items():
        dong_results.append({
            'cluster': cluster_id,
            'dong': dong,
            'count': count,
            'ratio': count / total_in_cluster
        })

sigungu_df = pd.DataFrame(sigungu_results)
dong_df = pd.DataFrame(dong_results)

print(f"지역 분포 분석 완료:")
print(f"  - sigungu: {len(sigungu_df)}개 레코드")
print(f"  - dong: {len(dong_df)}개 레코드")

# ============================================================================
# 8. 결과 저장
# ============================================================================
print("\n[8] 결과 저장 중...")

# 클러스터 라벨과 public_id 매핑 저장
cluster_mapping.to_csv(
    os.path.join(result_csv_dir, 'cluster_labels_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_labels_with_outlier_removal.csv")

# 매출 이상치 업장 정보 저장
if len(outlier_stores) > 0:
    outlier_stores.to_csv(
        os.path.join(result_csv_dir, 'sales_outlier_stores.csv'), 
        index=False, 
        encoding='utf-8-sig'
    )
    print("저장 완료: sales_outlier_stores.csv")
    
    # # 이상치 제거 통계 요약
    # outlier_summary = pd.DataFrame({
    #     'metric': ['제외된 업장 수', '정상 업장 수', '전체 업장 수', 
    #                '이상치 하한선 (Q1-1.5*IQR)', '이상치 상한선 (Q3+1.5*IQR)',
    #                '이상치 업장 평균 매출', '정상 업장 평균 매출'],
    #     'value': [
    #         len(outlier_stores),
    #         len(normal_stores),
    #         len(store_sales_df),
    #         lower_bound,
    #         upper_bound,
    #         outlier_stores['avg_sales_card'].mean() if len(outlier_stores) > 0 else 0,
    #         normal_stores['avg_sales_card'].mean() if len(normal_stores) > 0 else 0
    #     ]
    # })
    outlier_summary = pd.DataFrame({
        'metric': ['제외된 업장 수', '정상 업장 수', '전체 업장 수', 
                   '제거 비율 (%)', '하위 임계값 (percentile)', '상위 임계값 (percentile)',
                   '이상치 하한선', '이상치 상한선',
                   '이상치 업장 평균 매출', '정상 업장 평균 매출'],
        'value': [
            len(outlier_stores),
            len(normal_stores),
            len(store_sales_df),
            outlier_ratio,
            lower_percentile,
            upper_percentile,
            lower_bound,
            upper_bound,
            outlier_stores['avg_sales_card'].mean() if len(outlier_stores) > 0 else 0,
            normal_stores['avg_sales_card'].mean() if len(normal_stores) > 0 else 0
        ]
    })
    outlier_summary.to_csv(
        os.path.join(result_csv_dir, 'sales_outlier_removal_summary.csv'), 
        index=False, 
        encoding='utf-8-sig'
    )
    print("저장 완료: sales_outlier_removal_summary.csv")

# 클러스터별 업장 분포 저장 (각 카테고리별로 별도 파일)
depth_1_df.to_csv(
    os.path.join(result_csv_dir, 'cluster_depth_1_distribution_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_depth_1_distribution_with_outlier_removal.csv")

depth_2_df.to_csv(
    os.path.join(result_csv_dir, 'cluster_depth_2_distribution_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_depth_2_distribution_with_outlier_removal.csv")

depth_3_df.to_csv(
    os.path.join(result_csv_dir, 'cluster_depth_3_distribution_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_depth_3_distribution_with_outlier_removal.csv")

# 클러스터별 지역 분포 저장 (각 지역별로 별도 파일)
sigungu_df.to_csv(
    os.path.join(result_csv_dir, 'cluster_sigungu_distribution_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_sigungu_distribution_with_outlier_removal.csv")

dong_df.to_csv(
    os.path.join(result_csv_dir, 'cluster_dong_distribution_with_outlier_removal.csv'), 
    index=False, 
    encoding='utf-8-sig'
)
print("저장 완료: cluster_dong_distribution_with_outlier_removal.csv")

print("\n" + "=" * 80)
print("모든 작업 완료! (이상치 제거 버전)")
print("=" * 80)
print(f"\n생성된 파일:")
print("  - cluster_labels_with_outlier_removal.csv")
print("  - sales_outlier_stores.csv (제외된 매출 이상치 업장)")
print("  - sales_outlier_removal_summary.csv (이상치 제거 통계 요약)")
print("  - cluster_depth_1_distribution_with_outlier_removal.csv")
print("  - cluster_depth_2_distribution_with_outlier_removal.csv")
print("  - cluster_depth_3_distribution_with_outlier_removal.csv")
print("  - cluster_sigungu_distribution_with_outlier_removal.csv")
print("  - cluster_dong_distribution_with_outlier_removal.csv")
print("  - cluster_timeseries_with_outlier_removal.png")
print("  - cluster_distribution_with_outlier_removal.png")
print("\n매출 이상치 제거 전후 비교:")
print(f"  원본 시계열 수: {len(mySeries_filtered)}")
print(f"  매출 이상치 제거 후: {len(mySeries_cleaned)}")
print(f"  제외된 업장 수: {len(mySeries_filtered) - len(mySeries_cleaned)}")
print(f"  제외 비율: {(len(mySeries_filtered) - len(mySeries_cleaned)) / len(mySeries_filtered) * 100:.2f}%")

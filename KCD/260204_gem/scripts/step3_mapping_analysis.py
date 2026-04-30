"""
Step 3: UDX 코드 생성 및 설명 요인 분석
- Input 1: inflection_p1p2_labels.csv (Step 1 결과)
- Input 2: store_features_for_analysis.csv (기존 피처)
- Output: UDX_analysis_report.csv (코드별 통계), 회귀분석 결과
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from pathlib import Path

# 한글 폰트 설정
import platform
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 1. 설정 및 데이터 로드
# ==========================================
TABLES_DIR = Path("../outputs/tables")
TABLES_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 로딩 중...")
# Step 1에서 만든 변곡점 결과
df_inflection = pd.read_csv("../outputs/tables/inflection_p1p2_labels.csv") 

# 기존 피처 및 클러스터 정보
df_features = pd.read_csv("../../basic_data/store_features_for_analysis.csv")

# 데이터 병합
df_final = pd.merge(df_features, df_inflection[['public_id', 'P1_label', 'P2_label']], on='public_id', how='inner')
print(f"병합 완료: {len(df_final)}개 업장")

# ==========================================
# 2. UDX 코드 생성 (Mapping)
# ==========================================
# [중요] K=6 클러스터를 X, Y, Z로 매핑 (사용자 정의)
# 0,5 -> X (성장) / 2,3 -> Y (안정) / 1,4 -> Z (쇠퇴)
def map_pattern(cluster_id):
    if cluster_id in [0, 5]: return 'X'
    elif cluster_id in [2, 3]: return 'Y'
    else: return 'Z' # 1, 4

df_final['Pattern_label'] = df_final['cluster'].apply(map_pattern)

# 최종 3자리 코드 생성 (예: UUX)
df_final['UDX_Code'] = df_final['P1_label'] + df_final['P2_label'] + df_final['Pattern_label']

print("\n=== UDX 코드 분포 ===")
print(df_final['UDX_Code'].value_counts())

# ==========================================
# 3. 설명 변수 분석 (Explanation)
# ==========================================
explain_cols = ['new_customer_ratio', 'cv_sales_card', 'business_density', 'business_age_months']

# 코드별 평균값 계산
summary = df_final.groupby('UDX_Code')[explain_cols].mean()
summary['count'] = df_final['UDX_Code'].value_counts()
summary = summary.sort_values('new_customer_ratio', ascending=False)

print("\n=== 코드별 주요 변수 평균 (상위 5개) ===")
print(summary.head())
summary.to_csv("../outputs/tables/UDX_analysis_report.csv")

# 시각화: 신규 고객 비율 비교
plt.figure(figsize=(12, 6))
sns.barplot(x='UDX_Code', y='new_customer_ratio', data=df_final, 
            order=summary.index, palette='viridis')
plt.title("생애주기 코드별 신규 고객 유입 비율 (New Customer Ratio)")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("../outputs/figures/UDX_new_customer.png")
print("그래프 저장 완료: ../outputs/figures/UDX_new_customer.png")

# ==========================================
# 4. 통계적 검증 (Regression)
# ==========================================
# 타겟: 성장형 코드(X가 포함된 코드)인지 여부
df_final['Is_Growth'] = df_final['Pattern_label'].apply(lambda x: 1 if x == 'X' else 0)

# 로지스틱 회귀
X = df_final[explain_cols]
X = sm.add_constant(X)
y = df_final['Is_Growth']

try:
    model = sm.Logit(y, X).fit(disp=0)
    print("\n=== [통계 검증] 성장형(X) 결정 요인 분석 ===")
    print(model.summary())
    
    # 핵심 결과 해석 출력
    coef_new = model.params['new_customer_ratio']
    print(f"\n[핵심 발견] 신규 고객 비율이 1단위 증가할 때, 성장형일 확률(Log Odds)은 {coef_new:.2f} 증가합니다.")
except Exception as e:
    print(f"회귀분석 에러: {e}")
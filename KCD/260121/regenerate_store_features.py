"""
시계열 특성 변수 추출
결정요인 분석을 위한 시계열 특성 및 집계 변수 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("시계열 특성 변수 추출")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

weekly_df = pd.read_parquet('original_data/weekly.parquet')
meta_df = pd.read_csv('original_data/meta.csv')
cluster_labels = pd.read_csv('260121/result_csv/cluster_labels.csv')

print(f"weekly.parquet: {weekly_df.shape}")
print(f"meta.csv: {meta_df.shape}")
print(f"cluster_labels: {cluster_labels.shape}")

# date_id를 datetime으로 변환
weekly_df['date_id'] = pd.to_datetime(weekly_df['date_id'])

# day_after1 계산
min_date = weekly_df['date_id'].min()
weekly_df['day_after1'] = ((weekly_df['date_id'] - min_date).dt.days // 7) + 1
weekly_df = weekly_df[weekly_df['day_after1'] != 0]

print("데이터 로드 완료")

# ============================================================================
# 2. 업장별 시계열 특성 추출
# ============================================================================
print("\n[2] 업장별 시계열 특성 추출 중...")

features_list = []

for public_id in weekly_df['public_id'].unique():
    store_data = weekly_df[weekly_df['public_id'] == public_id].sort_values('day_after1')
    
    if len(store_data) < 10:  # 최소 10주 이상만 분석
        continue
    
    # 기본 통계
    total_weeks = len(store_data)
    avg_sales_card = store_data['sales_card'].mean()
    std_sales_card = store_data['sales_card'].std()
    cv_sales_card = std_sales_card / avg_sales_card if avg_sales_card > 0 else 0  # 변동계수
    
    # 성장률 (초기 25% vs 후기 25%)
    early_period = store_data.head(max(1, total_weeks // 4))
    late_period = store_data.tail(max(1, total_weeks // 4))
    early_avg = early_period['sales_card'].mean()
    late_avg = late_period['sales_card'].mean()
    growth_rate = (late_avg - early_avg) / early_avg if early_avg > 0 else 0
    
    # 매출 추세 (선형 회귀 기울기)
    if len(store_data) > 1:
        x = np.arange(len(store_data))
        y = store_data['sales_card'].values
        trend_slope = np.polyfit(x, y, 1)[0] / avg_sales_card if avg_sales_card > 0 else 0
    else:
        trend_slope = 0
    
    # 계절성 (주말 매출 비율)
    if 'weekend_sales' in store_data.columns:
        weekend_ratio = store_data['weekend_sales'].mean()
    else:
        weekend_ratio = np.nan
    
    # 고객 관련
    if 'customer' in store_data.columns:
        avg_customer = store_data['customer'].mean()
        std_customer = store_data['customer'].std()
        cv_customer = std_customer / avg_customer if avg_customer > 0 else 0
        
        if 'customer_new' in store_data.columns:
            avg_new_customer = store_data['customer_new'].mean()
            new_customer_ratio = avg_new_customer / avg_customer if avg_customer > 0 else 0
        else:
            new_customer_ratio = np.nan
    else:
        avg_customer = np.nan
        cv_customer = np.nan
        new_customer_ratio = np.nan
    
    # 매출 구조
    total_sales = store_data['sales_card'].sum()
    if 'sales_invoice' in store_data.columns:
        total_invoice = store_data['sales_invoice'].sum()
        card_ratio = total_sales / (total_sales + total_invoice) if (total_sales + total_invoice) > 0 else 0
    else:
        card_ratio = 1.0
    
    if 'sales_delivery' in store_data.columns:
        total_delivery = store_data['sales_delivery'].sum()
        delivery_ratio = total_delivery / total_sales if total_sales > 0 else 0
    else:
        delivery_ratio = np.nan
    
    # 시간대별 매출 패턴
    if 'before_noon_sales' in store_data.columns:
        before_noon_avg = store_data['before_noon_sales'].mean()
        after_noon_avg = store_data['after_noon_sales'].mean() if 'after_noon_sales' in store_data.columns else np.nan
    else:
        before_noon_avg = np.nan
        after_noon_avg = np.nan
    
    # 최대/최소 매출
    max_sales = store_data['sales_card'].max()
    min_sales = store_data['sales_card'].min()
    max_min_ratio = max_sales / min_sales if min_sales > 0 else 0
    
    features_list.append({
        'public_id': public_id,
        'total_weeks': total_weeks,
        'avg_sales_card': avg_sales_card,
        'std_sales_card': std_sales_card,
        'cv_sales_card': cv_sales_card,
        'growth_rate': growth_rate,
        'trend_slope': trend_slope,
        'weekend_ratio': weekend_ratio,
        'avg_customer': avg_customer,
        'cv_customer': cv_customer,
        'new_customer_ratio': new_customer_ratio,
        'card_ratio': card_ratio,
        'delivery_ratio': delivery_ratio,
        'before_noon_ratio': before_noon_avg,
        'after_noon_ratio': after_noon_avg,
        'max_sales': max_sales,
        'min_sales': min_sales,
        'max_min_ratio': max_min_ratio
    })

ts_features = pd.DataFrame(features_list)
print(f"시계열 특성 추출 완료: {len(ts_features)}개 업장")

# ============================================================================
# 3. 업장 특성 변수 추출 (메타데이터)
# ============================================================================
print("\n[3] 업장 특성 변수 추출 중...")

# 메타데이터에서 업장 특성 추출
store_features = meta_df[['public_id', 'sigungu', 'dong', 
                          'business_square_size', 'delivery_link', 
                          'age', 'open_month',
                          'classification__kcd_v3__depth_1_name',
                          'classification__kcd_v3__depth_2_name',
                          'classification__kcd_v3__depth_3_name']].copy()

# 컬럼명 간소화
store_features = store_features.rename(columns={
    'classification__kcd_v3__depth_1_name': 'depth_1',
    'classification__kcd_v3__depth_2_name': 'depth_2',
    'classification__kcd_v3__depth_3_name': 'depth_3'
})

# 영업 기간 계산 (개업월 기준)
store_features['open_month'] = pd.to_datetime(store_features['open_month'], errors='coerce')
reference_date = pd.to_datetime('2023-08-28')
store_features['business_age_months'] = ((reference_date - store_features['open_month']).dt.days / 30).fillna(0)
store_features['business_age_months'] = store_features['business_age_months'].clip(lower=0)

# 연령대를 숫자로 변환
age_mapping = {
    '10대': 1, '20대': 2, '30대': 3, '40대': 4, '50대': 5, '60대 이상': 6
}
store_features['age_numeric'] = store_features['age'].map(age_mapping).fillna(0)

print(f"업장 특성 추출 완료: {len(store_features)}개 업장")

# ============================================================================
# 4. 지역 집계 특성 생성
# ============================================================================
print("\n[4] 지역 집계 특성 생성 중...")

# weekly_df에 지역 정보 추가 (meta_df와 조인)
weekly_with_region = weekly_df.merge(
    meta_df[['public_id', 'sigungu', 'dong']],
    on='public_id',
    how='left'
)

# 동별 집계
dong_agg = weekly_with_region.groupby('dong').agg({
    'public_id': 'nunique',
    'sales_card': 'mean'
}).reset_index()
dong_agg.columns = ['dong', 'dong_store_count', 'dong_avg_sales']

# 시군구별 집계
sigungu_agg = weekly_with_region.groupby('sigungu').agg({
    'public_id': 'nunique',
    'sales_card': 'mean'
}).reset_index()
sigungu_agg.columns = ['sigungu', 'sigungu_store_count', 'sigungu_avg_sales']

# 동별 업종 밀도
meta_df_temp = meta_df.copy()
meta_df_temp['depth_2'] = meta_df_temp['classification__kcd_v3__depth_2_name']
dong_business_density = meta_df_temp.groupby(['dong', 'depth_2']).size().reset_index(name='count')
dong_total = meta_df_temp.groupby('dong').size().reset_index(name='total')
dong_business_density = dong_business_density.merge(dong_total, on='dong')
dong_business_density['business_density'] = dong_business_density['count'] / dong_business_density['total']

# 각 업장의 동 내 업종 밀도 매칭
meta_with_density = meta_df_temp.merge(
    dong_business_density[['dong', 'depth_2', 'business_density']],
    on=['dong', 'depth_2'],
    how='left'
)

print("지역 집계 특성 생성 완료")

# ============================================================================
# 5. 모든 특성 통합
# ============================================================================
print("\n[5] 모든 특성 통합 중...")

# 시계열 특성 + 업장 특성
features = ts_features.merge(store_features, on='public_id', how='inner')

# 지역 집계 특성 추가
features = features.merge(dong_agg, on='dong', how='left')
features = features.merge(sigungu_agg, on='sigungu', how='left')

# 동 내 업종 밀도 추가
features = features.merge(
    meta_with_density[['public_id', 'business_density']],
    on='public_id',
    how='left'
)

# 클러스터 라벨 추가 (inner join: 클러스터 라벨이 있는 업장만 포함)
features = features.merge(cluster_labels, on='public_id', how='inner')

print(f"특성 통합 완료: {len(features)}개 업장, {len(features.columns)}개 변수")
print(f"클러스터 라벨이 있는 업장만 포함 (클러스터링 기준: 최소 95주 이상)")

# ============================================================================
# 6. 결측값 처리
# ============================================================================
print("\n[6] 결측값 처리 중...")

features['business_square_size'] = features['business_square_size'].fillna(features['business_square_size'].median())
features['delivery_link'] = features['delivery_link'].fillna(0)
features['business_density'] = features['business_density'].fillna(0)
features['dong_store_count'] = features['dong_store_count'].fillna(0)
features['dong_avg_sales'] = features['dong_avg_sales'].fillna(0)
features['sigungu_store_count'] = features['sigungu_store_count'].fillna(0)
features['sigungu_avg_sales'] = features['sigungu_avg_sales'].fillna(0)

# 숫자형 변수의 결측값을 0으로 대체 (cluster 제외)
numeric_cols = features.select_dtypes(include=[np.number]).columns
# cluster는 클러스터 라벨이므로 결측값 처리에서 제외
numeric_cols = [col for col in numeric_cols if col != 'cluster']
features[numeric_cols] = features[numeric_cols].fillna(0)

print("결측값 처리 완료")

# ============================================================================
# 7. 결과 저장
# ============================================================================
print("\n[7] 결과 저장 중...")

features.to_csv('basic_data/store_features_for_analysis.csv', index=False, encoding='utf-8-sig')
print("저장 완료: /basic_data/store_features_for_analysis.csv")

# 변수 설명 저장
variable_description = pd.DataFrame({
    'variable_name': features.columns.tolist(),
    'data_type': features.dtypes.astype(str).tolist(),
    'description': [
        '업장 고유 식별자',
        '총 영업 주수',
        '평균 카드 매출액',
        '카드 매출 표준편차',
        '카드 매출 변동계수 (CV)',
        '성장률 (후기/초기)',
        '매출 추세 기울기',
        '주말 매출 비율',
        '평균 고객 수',
        '고객 수 변동계수',
        '신규 고객 비율',
        '카드 매출 비율',
        '배달 매출 비율',
        '오전 매출 비율',
        '오후 매출 비율',
        '최대 매출액',
        '최소 매출액',
        '최대/최소 비율',
        '시군구',
        '동',
        '업장 규모 (㎡)',
        '배달 가능 여부 (0/1)',
        '연령대',
        '개업월',
        '업종 대분류',
        '업종 중분류',
        '업종 소분류',
        '영업 기간 (개월)',
        '연령대 (숫자)',
        '동 내 업장 수',
        '동 평균 매출액',
        '시군구 내 업장 수',
        '시군구 평균 매출액',
        '동 내 업종 밀도',
        '클러스터 라벨'
    ]
})

variable_description.to_csv('/basic_data/variable_description.csv', index=False, encoding='utf-8-sig')
print("저장 완료: /basic_data/variable_description.csv")

# ============================================================================
# 8. 요약 통계 출력
# ============================================================================
print("\n[8] 요약 통계:")

print(f"\n총 업장 수: {len(features)}")
print(f"총 변수 수: {len(features.columns)}")
print(f"\n클러스터별 분포:")
print(features['cluster'].value_counts().sort_index())

print(f"\n주요 변수 통계:")
key_vars = ['avg_sales_card', 'cv_sales_card', 'growth_rate', 'weekend_ratio', 
            'business_age_months', 'business_density']
for var in key_vars:
    if var in features.columns:
        print(f"\n{var}:")
        print(f"  평균: {features[var].mean():.4f}")
        print(f"  표준편차: {features[var].std():.4f}")
        print(f"  최소: {features[var].min():.4f}")
        print(f"  최대: {features[var].max():.4f}")

print("\n" + "=" * 80)
print("시계열 특성 추출 완료!")
print("=" * 80)

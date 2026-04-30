"""
시계열 클러스터링을 위한 데이터 전처리 및 저장 스크립트
weekly.parquet와 meta.csv를 사용하여 전처리된 데이터 파일 생성
"""

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("시계열 클러스터링용 데이터 준비 시작")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

weekly_df = pd.read_parquet('weekly.parquet')
meta_df = pd.read_csv('meta.csv')

print(f"weekly.parquet: {weekly_df.shape}")
print(f"meta.csv: {meta_df.shape}")

# public_id 일치 확인
weekly_public_ids = set(weekly_df['public_id'].unique())
meta_public_ids = set(meta_df['public_id'].unique())

print(f"\nweekly.parquet의 고유 public_id 수: {len(weekly_public_ids)}")
print(f"meta.csv의 고유 public_id 수: {len(meta_public_ids)}")
print(f"교집합 public_id 수: {len(weekly_public_ids & meta_public_ids)}")

# 교집합만 사용
common_public_ids = weekly_public_ids & meta_public_ids
weekly_df = weekly_df[weekly_df['public_id'].isin(common_public_ids)]
meta_df = meta_df[meta_df['public_id'].isin(common_public_ids)]

print(f"필터링 후 weekly_df: {weekly_df.shape}")
print(f"필터링 후 meta_df: {meta_df.shape}")

# ============================================================================
# 2. date_id를 순차적인 주 번호로 변환
# ============================================================================
print("\n[2] date_id를 순차적인 주 번호로 변환 중...")

# date_id를 datetime으로 변환
weekly_df['date_id'] = pd.to_datetime(weekly_df['date_id'])

# date_id를 순차적인 주 번호로 변환 (day_after1과 유사)
# 최소 date_id를 1로 시작하는 주 번호로 변환
min_date = weekly_df['date_id'].min()
weekly_df['day_after1'] = ((weekly_df['date_id'] - min_date).dt.days // 7) + 1

print(f"day_after1 범위: {weekly_df['day_after1'].min()} ~ {weekly_df['day_after1'].max()}")

# day_after1=0 제외 (기존 노트북과 동일)
weekly_df = weekly_df[weekly_df['day_after1'] != 0]

# ============================================================================
# 3. sales_ratio 계산
# ============================================================================
print("\n[3] sales_ratio 계산 중...")

# sales_ratio 계산: 각 업장의 주별 매출을 전체 매출 대비 비율로 정규화
# 주별 전체 매출 계산
weekly_total_sales = weekly_df.groupby('day_after1')['sales_card'].sum()
weekly_df = weekly_df.merge(weekly_total_sales.reset_index().rename(columns={'sales_card': 'total_sales'}), 
                            on='day_after1', how='left')

# 0으로 나누기 방지
weekly_df['sales_ratio'] = weekly_df['sales_card'] / weekly_df['total_sales'].replace(0, np.nan)

# NaN 값 제거 (total_sales가 0인 경우)
weekly_df = weekly_df.dropna(subset=['sales_ratio'])

print(f"sales_ratio 계산 완료")
print(f"sales_ratio 범위: {weekly_df['sales_ratio'].min():.6f} ~ {weekly_df['sales_ratio'].max():.6f}")

# ============================================================================
# 4. 필요한 컬럼만 선택하여 저장
# ============================================================================
print("\n[4] 전처리된 데이터 저장 중...")

# weekly 데이터: 클러스터링에 필요한 컬럼만 선택
weekly_processed = weekly_df[['public_id', 'date_id', 'day_after1', 'sales_card', 'sales_ratio']].copy()

# meta 데이터: 필요한 컬럼만 선택
meta_processed = meta_df[[
    'public_id', 
    'sigungu', 
    'dong',
    'classification__kcd_v3__depth_1_name',
    'classification__kcd_v3__depth_2_name',
    'classification__kcd_v3__depth_3_name'
]].copy()

# 컬럼명 간소화 (선택사항)
meta_processed = meta_processed.rename(columns={
    'classification__kcd_v3__depth_1_name': 'depth_1',
    'classification__kcd_v3__depth_2_name': 'depth_2',
    'classification__kcd_v3__depth_3_name': 'depth_3'
})

# 저장
weekly_processed.to_parquet('weekly_processed.parquet', index=False)
meta_processed.to_csv('meta_processed.csv', index=False, encoding='utf-8-sig')

print(f"저장 완료:")
print(f"  - weekly_processed.parquet: {weekly_processed.shape}")
print(f"  - meta_processed.csv: {meta_processed.shape}")

# ============================================================================
# 5. 통계 정보 출력
# ============================================================================
print("\n[5] 데이터 통계 정보:")

print(f"\nweekly_processed 통계:")
print(f"  - 고유 public_id 수: {weekly_processed['public_id'].nunique()}")
print(f"  - day_after1 범위: {weekly_processed['day_after1'].min()} ~ {weekly_processed['day_after1'].max()}")
print(f"  - 총 레코드 수: {len(weekly_processed)}")

print(f"\nmeta_processed 통계:")
print(f"  - 고유 public_id 수: {meta_processed['public_id'].nunique()}")
print(f"  - depth_1 카테고리 수: {meta_processed['depth_1'].nunique()}")
print(f"  - depth_2 카테고리 수: {meta_processed['depth_2'].nunique()}")
print(f"  - depth_3 카테고리 수: {meta_processed['depth_3'].nunique()}")
print(f"  - sigungu 수: {meta_processed['sigungu'].nunique()}")
print(f"  - dong 수: {meta_processed['dong'].nunique()}")

# public_id별 시계열 길이 통계
series_lengths = weekly_processed.groupby('public_id').size()
print(f"\n시계열 길이 통계:")
print(f"  - 평균 길이: {series_lengths.mean():.2f}")
print(f"  - 최소 길이: {series_lengths.min()}")
print(f"  - 최대 길이: {series_lengths.max()}")
print(f"  - 중앙값: {series_lengths.median():.2f}")
print(f"  - 95개 이상인 시계열 수: {(series_lengths >= 95).sum()}")

print("\n" + "=" * 80)
print("데이터 준비 완료!")
print("=" * 80)
print("\n생성된 파일:")
print("  - weekly_processed.parquet: 전처리된 시계열 데이터")
print("  - meta_processed.csv: 전처리된 메타데이터")
print("\n이제 time_series_clustering_analysis.py를 실행하여 클러스터링을 수행할 수 있습니다.")

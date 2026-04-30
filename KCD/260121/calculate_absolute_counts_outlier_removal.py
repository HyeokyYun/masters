"""
클러스터별 업종 및 지역 분포의 절대수 계산
각 카테고리 값(예: depth_1="외식업", sigungu="강남구")에 대해
클러스터 내 개수(cluster_count)와 전체 개수(total_count)를 계산합니다.
"""

import pandas as pd
import numpy as np

print("=" * 80)
print("클러스터별 업종 및 지역 분포의 절대수 계산")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

# 클러스터 라벨과 메타데이터 로드
cluster_labels = pd.read_csv('/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/260121/result_csv/cluster_labels_with_outlier_removal.csv')
meta_df = pd.read_csv('/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1/original_data/meta_processed.csv')

# 클러스터 라벨과 메타데이터 결합
analysis_df = cluster_labels.merge(meta_df, on='public_id', how='left')

print(f"전체 데이터: {len(analysis_df)}개")
print(f"클러스터 수: {analysis_df['cluster'].nunique()}개")

# 전체 수가 1인 카테고리는 해석이 무의미하므로 제외
MIN_TOTAL_COUNT = 2

# ============================================================================
# 2. 업종(depth_1, depth_2, depth_3) 절대수 계산
# ============================================================================
print("\n[2] 업종별 절대수 계산 중...")

# depth_1 절대수
print("\n  - depth_1 계산 중...")
depth_1_total = analysis_df['depth_1'].value_counts().to_dict()
depth_1_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    cluster_depth_1 = cluster_data['depth_1'].value_counts()
    
    for depth_1, cluster_count in cluster_depth_1.items():
        total_count = depth_1_total.get(depth_1, 0)
        if total_count >= MIN_TOTAL_COUNT:
            depth_1_results.append({
                'cluster': cluster_id,
                'depth_1': depth_1,
                'cluster_count': cluster_count,
                'total_count': total_count,
            })

depth_1_df = pd.DataFrame(depth_1_results)
depth_1_df = depth_1_df.sort_values(['cluster', 'cluster_count'], ascending=[True, False])
print(f"    완료: {len(depth_1_df)}개 레코드")

# depth_2 절대수
print("\n  - depth_2 계산 중...")
depth_2_total = analysis_df['depth_2'].value_counts().to_dict()
depth_2_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    cluster_depth_2 = cluster_data['depth_2'].value_counts()
    
    for depth_2, cluster_count in cluster_depth_2.items():
        total_count = depth_2_total.get(depth_2, 0)
        if total_count >= MIN_TOTAL_COUNT:
            depth_2_results.append({
                'cluster': cluster_id,
                'depth_2': depth_2,
                'cluster_count': cluster_count,
                'total_count': total_count,
            })

depth_2_df = pd.DataFrame(depth_2_results)
depth_2_df = depth_2_df.sort_values(['cluster', 'cluster_count'], ascending=[True, False])
print(f"    완료: {len(depth_2_df)}개 레코드")

# depth_3 절대수
print("\n  - depth_3 계산 중...")
depth_3_total = analysis_df['depth_3'].value_counts().to_dict()
depth_3_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    cluster_depth_3 = cluster_data['depth_3'].value_counts()
    
    for depth_3, cluster_count in cluster_depth_3.items():
        total_count = depth_3_total.get(depth_3, 0)
        if total_count >= MIN_TOTAL_COUNT:
            depth_3_results.append({
                'cluster': cluster_id,
                'depth_3': depth_3,
                'cluster_count': cluster_count,
                'total_count': total_count,
            })

depth_3_df = pd.DataFrame(depth_3_results)
depth_3_df = depth_3_df.sort_values(['cluster', 'cluster_count'], ascending=[True, False])
print(f"    완료: {len(depth_3_df)}개 레코드")

# ============================================================================
# 3. 지역(sigungu, dong) 절대수 계산
# ============================================================================
print("\n[3] 지역별 절대수 계산 중...")

# sigungu 절대수
print("\n  - sigungu 계산 중...")
sigungu_total = analysis_df['sigungu'].value_counts().to_dict()
sigungu_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    cluster_sigungu = cluster_data['sigungu'].value_counts()
    
    for sigungu, cluster_count in cluster_sigungu.items():
        total_count = sigungu_total.get(sigungu, 0)
        if total_count >= MIN_TOTAL_COUNT:
            sigungu_results.append({
                'cluster': cluster_id,
                'sigungu': sigungu,
                'cluster_count': cluster_count,
                'total_count': total_count,
            })

sigungu_df = pd.DataFrame(sigungu_results)
sigungu_df = sigungu_df.sort_values(['cluster', 'cluster_count'], ascending=[True, False])
print(f"    완료: {len(sigungu_df)}개 레코드")

# dong 절대수
print("\n  - dong 계산 중...")
dong_total = analysis_df['dong'].value_counts().to_dict()
dong_results = []

for cluster_id in range(9):
    cluster_data = analysis_df[analysis_df['cluster'] == cluster_id]
    cluster_dong = cluster_data['dong'].value_counts()
    
    for dong, cluster_count in cluster_dong.items():
        total_count = dong_total.get(dong, 0)
        if total_count >= MIN_TOTAL_COUNT:
            dong_results.append({
                'cluster': cluster_id,
                'dong': dong,
                'cluster_count': cluster_count,
                'total_count': total_count,
            })

dong_df = pd.DataFrame(dong_results)
dong_df = dong_df.sort_values(['cluster', 'cluster_count'], ascending=[True, False])
print(f"    완료: {len(dong_df)}개 레코드")

# ============================================================================
# 4. 결과 저장
# ============================================================================
print("\n[4] 결과 저장 중...")

# 업종별 절대수 저장
depth_1_df.to_csv('cluster_depth_1_absolute_count_with_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("저장 완료: cluster_depth_1_absolute_count_with_outlier_removal.csv")

depth_2_df.to_csv('cluster_depth_2_absolute_count_with_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("저장 완료: cluster_depth_2_absolute_count_with_outlier_removal.csv")

depth_3_df.to_csv('cluster_depth_3_absolute_count_with_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("저장 완료: cluster_depth_3_absolute_count_with_outlier_removal.csv")

# 지역별 절대수 저장
sigungu_df.to_csv('cluster_sigungu_absolute_count_with_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("저장 완료: cluster_sigungu_absolute_count_with_outlier_removal.csv")

dong_df.to_csv('cluster_dong_absolute_count_with_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("저장 완료: cluster_dong_absolute_count_with_outlier_removal.csv")

# ============================================================================
# 5. 요약 통계 출력 (절대수 기준 상위 5개)
# ============================================================================
print("\n[5] 요약 통계 (절대수 기준 상위 5개):")

print("\n업종별 (depth_1) - 상위 5개:")
for cluster_id in range(9):
    cluster_data = depth_1_df[depth_1_df['cluster'] == cluster_id]
    if len(cluster_data) > 0:
        top5 = cluster_data.head(5)
        print(f"\n  Cluster {cluster_id}:")
        for _, row in top5.iterrows():
            print(f"    {row['depth_1']}: cluster_count={row['cluster_count']}, total_count={row['total_count']}")

print("\n업종별 (depth_2) - 상위 5개:")
for cluster_id in range(9):
    cluster_data = depth_2_df[depth_2_df['cluster'] == cluster_id]
    if len(cluster_data) > 0:
        top5 = cluster_data.head(5)
        print(f"\n  Cluster {cluster_id}:")
        for _, row in top5.iterrows():
            print(f"    {row['depth_2']}: cluster_count={row['cluster_count']}, total_count={row['total_count']}")

print("\n업종별 (depth_3) - 상위 5개:")
for cluster_id in range(9):
    cluster_data = depth_3_df[depth_3_df['cluster'] == cluster_id]
    if len(cluster_data) > 0:
        top5 = cluster_data.head(5)
        print(f"\n  Cluster {cluster_id}:")
        for _, row in top5.iterrows():
            print(f"    {row['depth_3']}: cluster_count={row['cluster_count']}, total_count={row['total_count']}")

print("\n지역별 (sigungu) - 상위 5개:")
for cluster_id in range(9):
    cluster_data = sigungu_df[sigungu_df['cluster'] == cluster_id]
    if len(cluster_data) > 0:
        top5 = cluster_data.head(5)
        print(f"\n  Cluster {cluster_id}:")
        for _, row in top5.iterrows():
            print(f"    {row['sigungu']}: cluster_count={row['cluster_count']}, total_count={row['total_count']}")

print("\n지역별 (dong) - 상위 5개:")
for cluster_id in range(9):
    cluster_data = dong_df[dong_df['cluster'] == cluster_id]
    if len(cluster_data) > 0:
        top5 = cluster_data.head(5)
        print(f"\n  Cluster {cluster_id}:")
        for _, row in top5.iterrows():
            print(f"    {row['dong']}: cluster_count={row['cluster_count']}, total_count={row['total_count']}")

print("\n" + "=" * 80)
print("모든 작업 완료!")
print("=" * 80)
print(f"\n생성된 파일:")
print("  - cluster_depth_1_absolute_count_with_outlier_removal.csv")
print("  - cluster_depth_2_absolute_count_with_outlier_removal.csv")
print("  - cluster_depth_3_absolute_count_with_outlier_removal.csv")
print("  - cluster_sigungu_absolute_count_with_outlier_removal.csv")
print("  - cluster_dong_absolute_count_with_outlier_removal.csv")
print("\n각 파일: cluster_count=클러스터 내 개수, total_count=전체 개수 (절대수).")

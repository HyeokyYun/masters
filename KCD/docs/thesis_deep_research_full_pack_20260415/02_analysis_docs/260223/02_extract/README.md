# Step 2: Signal Extraction

**목표**: `df_udx_labels.csv` (클러스터·변곡점·UDX 코드) 생성.

**입력**: 시계열 데이터 (Step 1 또는 원본 피벗).  
**참고**: 260204 run_02 (K-Shape), 260204_gem run_01_inflection_p1p2, step3_mapping.  
**산출**: `../outputs/tables/df_udx_labels.csv`.

기존 `store_cluster_labels_K6.parquet`, `inflection_p1p2_labels.csv`, `final_code_by_store_*.csv` 를 merge하여 생성 가능.

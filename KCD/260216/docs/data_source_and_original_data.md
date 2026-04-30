# 원본 데이터 vs store_features_for_analysis.csv

## 현재 구조

| 단계 | 사용 파일 | 비고 |
|------|-----------|------|
| **원본** | `original_data/weekly.parquet` (또는 weekly_processed.parquet), `original_data/meta.csv` (또는 meta_processed.csv) | 주별 매출·메타 |
| **피처 생성** | `260121/regenerate_store_features.py` | 원본을 읽어 매장별 집계·피처 계산 후 **260121 cluster_labels.csv를 병합**하여 저장 |
| **저장 결과** | `basic_data/store_features_for_analysis.csv` | 이미 **260121 클러스터 라벨이 포함된** 파생 테이블 |
| **260204** | `configs/base.yaml` → `features_csv: "../basic_data/store_features_for_analysis.csv"` | run_01, run_04, run_00_compare_* 등이 이 CSV를 읽음 |
| **260211** | `original_data/weekly_processed.parquet` + meta | **원본부터** `build_30w_features_and_labels.py`에서 30주 피처·라벨 직접 생성 |

즉, **260211은 원본부터** 진행하고, **260204 track A는 “이미 만들어진 CSV”**부터 시작합니다.

---

## 논문 관점에서의 문제

1. **재현성**  
   논문에서 “원본 데이터는 ~이다”라고 했을 때, 실제 분석이 **원본이 아니라** `store_features_for_analysis.csv`에서 시작하면, 독자가 같은 원본만으로는 동일 결과를 만들기 어렵습니다.  
   → **원본 정의**와 **“그 원본에서 위 CSV가 어떻게 만들어지는지”**가 논문/보조 자료에 있어야 합니다.

2. **클러스터 출처 혼재**  
   `store_features_for_analysis.csv`의 `cluster` 컬럼은 **260121** 클러스터링 결과가 미리 들어가 있습니다.  
   260204에서 run_02로 **K-Shape K6** 라벨을 새로 만들지만, run_01 → run_04가 쓰는 `data_features_clean.parquet`는 이 CSV에서 나오므로, **설정에 따라 260121 cluster가 쓰일 수** 있습니다.  
   → “성공률·ablation에서 쓰는 cluster가 어느 단계/어느 방법 결과인지”를 명확히 할 필요가 있습니다.

3. **일관성**  
   260211은 “원본 → 30주 피처”를 코드로 명시하고 있으므로, 260204도 “원본 → (필요 시) 피처 테이블”까지 한 번에 서술 가능하게 두는 편이 논문 서술과 맞습니다.

---

## 제 의견 (원본으로 진행해야 하냐)

- **결론: 논문에서는 “원본 데이터부터” 흐름을 명시하는 것이 맞습니다.**  
  다만 “지금 CSV를 버리고 전부 원본만 쓸 것인가”가 아니라, **다음 둘 중 하나를 선택**하면 됩니다.

### 선택 A: 현재처럼 CSV를 쓰되, 논문에서 원본과의 관계를 명시

- **원본**: `weekly_processed.parquet` + `meta_processed.csv` (또는 각각 weekly.parquet, meta.csv)로 정의.
- 논문/보고서에  
  **“매장별 피처는 위 원본 데이터로부터 260121/regenerate_store_features.py(또는 동일 로직)에 따라 생성하였으며, 그 결과를 store_features_for_analysis.csv로 사용하였다.”**  
  라고 적고, 필요하면 해당 스크립트를 “피처 생성 절차”로 인용.
- 이렇게 하면 **“사실상 원본에서 파생된 데이터를 쓰고 있지만, 그 파생 과정을 논문에서 명시”**하는 형태가 됩니다.  
  → **지금 구조를 크게 바꾸지 않고** 원본 기준 서술을 만족시킬 수 있습니다.

### 선택 B: 260204도 “원본 → 피처”를 코드로 통일 (권장 방향)

- **원본**을 260204 설정에서 지정하고,  
  **“원본 주별 + 메타만 넣으면, 매장별 피처 테이블(및 필요 시 data_features_clean)까지 만드는”** 스크립트를 260204(또는 공통 폴더)에 둡니다.
- 클러스터는 **CSV에 미리 넣지 않고**,  
  - run_02(또는 기존 클러스터 라벨 parquet) 결과를 **나중에** 피처 테이블에 merge하는 방식으로 통일합니다.  
  → 성공률·ablation에서 쓰는 cluster가 “260204 K-Shape K6”인지 “260121”인지 설정 한 곳에서만 결정되게 할 수 있습니다.
- 이렇게 하면 논문에  
  **“분석은 원본(주별·메타)에서 시작하며, 매장별 피처는 [해당 스크립트]로 생성하고, 클러스터는 [run_02/260121] 결과를 병합하였다.”**  
  라고 **한 번에** 쓸 수 있고, 재현 시에도 “원본 + 이 스크립트 + 클러스터 라벨”만 있으면 됩니다.

---

## 요약

- **원본데이터로 진행해야 하냐?**  
  → **논문/재현성 관점에서는 “원본 데이터부터의 흐름”을 반드시 명시하는 것이 맞고**, 그에 따라 (A) CSV 사용을 인정하되 “원본에서의 생성 절차”를 문서화하거나, (B) 260204에서 원본 → 피처 생성까지 한 번에 수행하도록 맞추는 쪽을 권장합니다.
- **지금 당장**은  
  - 260216이나 논문 보조 문서에 **“원본 = weekly_processed.parquet + meta_processed.csv”**와 **“store_features_for_analysis.csv는 260121/regenerate_store_features.py로 원본에서 생성”**이라고 적어 두고,  
  - 중장기로는 **(B)처럼 원본 → 피처를 260204 한 곳에서 수행**하고, cluster는 별도 라벨 파일로만 merge하는 구조로 정리하는 것을 추천합니다.

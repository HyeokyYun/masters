# 260319_codex

`260319_codex`는 사용자가 정의한 생애주기 코드 체계를 그대로 구현하기 위한 새 실험 폴더입니다.

## 핵심 레이블 규칙

- `U` = 상승
- `D` = 하락
- `X` = 전체 추세 상승
- `Y` = 전체 추세 유지
- `Z` = 전체 추세 하락

즉 최종 코드는 다음 구조를 따릅니다.

```text
final_code = P1_label + P2_label + Pattern_label
```

- `P1_label`: 전반부 기울기 방향 (`U`/`D`)
- `P2_label`: 후반부 기울기 방향 (`U`/`D`)
- `Pattern_label`: 시작 구간 대비 종료 구간의 전체 패턴 (`X`/`Y`/`Z`)

예시:

- `UUX`: 전반 상승, 후반 상승, 전체 추세 상승
- `DUY`: 전반 하락, 후반 상승, 전체 추세 유지
- `DDZ`: 전반 하락, 후반 하락, 전체 추세 하락

## 구성

- `src/step01_preprocessing.py`
  - 원천 데이터 로드
  - 개업시점 정렬
  - 결측 보간
  - STL 분해
  - MinMax 정규화
- `src/step02_feature_extraction.py`
  - 업장별 시계열 피처 생성
  - 전반/후반/전체 기울기
  - 시작/종료 평균과 전체 변화율
- `src/step03_label_assignment.py`
  - `P1_label`, `P2_label`, `Pattern_label`
  - `final_code`
  - `life_cycle_category`
- `src/step04_clustering.py`
  - 정규화 매출 궤적 기반 클러스터링
  - KMeans / DTW-KMeans / K-Shape 비교
  - `final_code`, `Pattern_label`과의 교차표 저장
- `src/step05_modeling.py`
  - `final_code`를 종속변수로 한 MNLogit
  - GBM + SHAP 요인 분석
  - `Pattern_label` 기준 PSM 보조분석
- `src/step06_prediction.py`
  - 오픈 후 30주 early feature 생성
  - `final_code` 조기예측
  - Ablation, 교차검증 성능, SHAP 저장

## 실행

```bash
cd 260319_codex
python main.py
```

특정 단계만 다시 실행하려면:

```bash
python main.py --step 4
python main.py --step 6
```

## 주요 출력

- `outputs/tables/store_features.csv`
- `outputs/tables/store_features_labeled.csv`
- `outputs/tables/pattern_distribution.csv`
- `outputs/tables/final_code_distribution.csv`
- `outputs/tables/final_code_feature_means.csv`
- `outputs/tables/cluster_evaluation.csv`
- `outputs/tables/cluster_method_comparison.csv`
- `outputs/tables/final_code_cluster_crosstab.csv`
- `outputs/tables/mnlogit_summary.txt`
- `outputs/tables/gbm_feature_importance.csv`
- `outputs/tables/ablation_early_prediction_final_code.csv`
- `outputs/tables/prediction_full_evaluation_final_code.csv`

# 260301 — 석사논문 통합 파이프라인

**목적**: original_data 기반으로 전체 실험을 재검증하고, 석사논문 스토리에 맞춰 순차 실행.

**기본 데이터**: `../original_data/`
- `weekly.parquet` — 주별 매출·고객(customer, customer_new) — store_features 생성용
- `weekly_processed.parquet` — 주별 매출(sales_card, day_after1) — 클러스터링·예측용
- `meta.csv`, `meta_processed.csv` — 업장 메타

---

## 실행 순서

```bash
cd 26-1
source .venv/bin/activate
python 260301/run_all.py
```

또는 단계별:
```bash
python 260301/01_verify_data/run_verify_original_data.py
python 260301/02_preprocess/run_build_base_features.py
python 260301/03_clustering_udx/run_merge_labels.py
python 260301/04_summary_regression/run_summary_and_multinomial.py
python 260301/05_prediction/run_30w_prediction.py
# (선택) 첫 30주 회귀
python 260225/03_regression_30w/run_regression_30w_only.py
```

---

## 폴더 구조

```
260301/
├── README.md
├── run_all.py
├── configs/
│   └── pipeline.yaml
├── 01_verify_data/      # original_data 검증
├── 02_preprocess/       # base features (기존 260204/260223 활용)
├── 03_clustering_udx/   # K6 + final_code 병합
├── 04_summary_regression/  # Summary Stats + Multinomial Logit
├── 05_prediction/       # 30주 예측
├── outputs/
└── docs/
    ├── 00_전체검토_및_실험점검.md
    └── 01_석사논문_스토리_스텝정리.md
```

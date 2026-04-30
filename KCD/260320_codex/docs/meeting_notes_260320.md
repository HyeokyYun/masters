# 2026-03-20 개별연구 미팅 반영 (260320_codex)

## 교수님 피드백 요지

1. **매출 변동성(`cv_sales_card`) 정의**  
   단순 `표준편차/평균`은 매출이 성장 추세일 때 평균이 시계열 중간에 있어 변동성이 과대 해석될 수 있음.  
   → **추세(선형 또는 곡선)에 대한 잔차** 기준으로 변동성을 재정의할 것.  
   (`run_01_trend_residual_cv.py`: 선형·2차 다항 추세 적합 후 잔차 SD / 평균|매출|)

2. **업종×상권 경쟁(밀도) 상호작용**  
   패스트푸드·카페 등 효과가 동네에 같은 업종이 몇 개나 있는지에 따라 달라질 수 있음.  
   → 동 단위 `dens_{업종}` = (해당 동·해당 depth_2 점포 수) / (동 전체 점포 수),  
   및 `depth_더미 × dens_{동일업종}` 상호작용 (`run_02`, `run_03`)

3. **체인/프랜차이즈**  
   데이터 공백·불명확이 많으면 **사용하지 않거나** 별도 표기. (본 폴더에서는 미구현)

4. **대표자 연령·성별**  
   `meta.csv`에 `age`는 혼합 형식(연령대, 생년월일 등) → **수치화 시도** (`owner_age_numeric`).  
   **성별 컬럼은 현재 meta에 없음** — 추가 데이터가 있으면 병합 가능.

5. **업력 짧은 점포만 서브샘플**  
   신규 창업 관점에서 업력 6·12·24개월 이하 등으로 나눠 재추정. (`run_04_subsample_by_age.py`)  
   업력 분포 히스토그램 (`run_05_business_age_histogram.py`)

6. **조기예측(30주) F1 ~0.37**  
   “스몰 비즈니스 세일즈 포캐스트” 문헌에서 **어떤 수준이 좋은지 기준**을 별도 조사.  
   → `docs/forecasting_literature_notes.md` 참고

7. **다항 로짓 기준 세 가지(Stable / Growth / Decline)**  
   같은 우도 모형, 기준만 바꾼 것. 이론적으로 일관된 해석. (기존 260301과 동일)

## 실행 순서

```bash
# 프로젝트 루트에서
./.venv/bin/python 260320_codex/run_05_business_age_histogram.py
./.venv/bin/python 260320_codex/run_01_trend_residual_cv.py
./.venv/bin/python 260320_codex/run_02_build_extended_dataset.py
./.venv/bin/python 260320_codex/run_03_extended_mnlogit.py
./.venv/bin/python 260320_codex/run_04_subsample_by_age.py
```

또는 `./.venv/bin/python 260320_codex/run_all.py`

## 선행 조건

- `260301/01_verify_data/outputs/tables/df_for_multinomial_logit.csv` (또는 이전 산출물 폴백)  
- `original_data/weekly.parquet` (Step 1용)  
- `original_data/meta.csv` (연령 병합용)

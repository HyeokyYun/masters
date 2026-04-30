# KCD 소상공인 라이프사이클 연구 — Claude 작업 가이드

## 연구 맥락
- **지도교수**: KAIST 김지희 교수
- **데이터**: KCD(한국신용데이터) — 서울 음식점 59,089개 점포, 주간 매출 2021-01-01 ~ 2023-08-28
- **투고 타깃**: HICSS 2027 (유력) / ICIS 2026 / DSS 저널 확장판 (2027)
- **연구 주제**: Data-Driven Early Warning System for Small Business Lifecycle Prediction
- **데이터 민감성**: KCD 원본은 외부 비공개. 논문/스니펫 공유 전 데이터 출판 허가 여부를 항상 확인할 것.

## 디렉토리 규칙
- **활성 작업 영역**: `top_tier/` — 코드/출력/논문 드래프트 모두 여기.
- **레거시 아카이브**: `260121`, `260204`, …, `260409` 등 날짜 폴더는 과거 반복 실험. **수정·삭제 금지**, 참조만.
- **출력 규약**: 모든 산출물은 `top_tier/outputs/{tables,figures,docs}`에 저장.
  - `tables/`: parquet, csv
  - `figures/`: png, pdf
  - `docs/`: 실행 로그(`stepXX.log`), 보고서 md
- **논문 드래프트**: `top_tier/paper_draft/0X_*.md` — 섹션 단위로 구성.
- **지도교수 미팅 메모**: `top_tier/advisor_meeting/`.

## 실행 환경
- **Python 인터프리터**: 항상 `/home/hyeoky98/miniforge/bin/python` 사용. `python3` / `.venv` 사용 금지.
- **주요 패키지**: pandas, numpy, scikit-learn, statsmodels, lightgbm, xgboost, lifelines, shap, torch (CPU 권장 — `FORCE_CPU=1`).
- **장기 실행 패턴**:
  ```
  PYTHONUNBUFFERED=1 nohup /home/hyeoky98/miniforge/bin/python \
    /home/hyeoky98/kcd/top_tier/src/stepXX_*.py \
    2>&1 | tee /home/hyeoky98/kcd/top_tier/outputs/docs/stepXX.log &
  ```
- **공통 설정**: `top_tier/config.py` — 경로·시드(42)·outcome class 정의를 항상 import해서 재사용. 하드코딩 금지.

## 파이프라인 개요 (참조용)
- step00–01: 원본 패널 준비, 데이터 기반 통합
- step02(b): 생존분석 (Kaplan-Meier, Cox PH + 가정 검정)
- step03: 예측 모델 (XGBoost 베이스라인)
- step04: 시계열 클러스터링 (K-Means / K-Shape)
- step05(b,c): 인과 분석 (Granger, DiD event study, 강화 PSM)
- step06: SHAP 해석
- step07: 견고성 점검
- step08–09: figure / report 생성
- step10(b): hybrid 예측 (leakage-free 변형)
- step11: 변동성 패러독스 분해
- step12: Early Warning System 산출
- step13(b): DL 베이스라인 (LSTM/GRU/Transformer)
- step14: Figure 1 framework
- step15: external validation
- audit01–04: 자기 감사 (outcome sanity, trivial baseline, threshold sensitivity, cluster external validity)

## 작업 스타일
- **응답 언어**: 한국어 기본. 코드 주석/논문 본문은 영어.
- **다중 LLM 병용**: 유저는 GPT/Claude/Gemini를 교차 활용. 초안·outline 형태가 환영됨. "Claude만이 답이다" 식 단정 금지.
- **논문 톤**: ICIS/HICSS reviewer 가독성 — IS·DSR 어휘, 인용은 author-year placeholder 허용.
- **수치 인용**: 본문에 등장하는 모든 수치는 `outputs/tables/` 또는 로그에서 출처 확인 후 인용. 추정·반올림 시 명시.

## 가드레일
- **레거시 폴더 수정 금지**: `260MMDD*` 폴더는 읽기 전용으로 취급.
- **원본 데이터 덮어쓰기 금지**: `original_data/weekly.parquet`, `original_data/meta.csv`는 read-only.
- **모델 재학습 전 확인**: step02·03·10·13 등은 수십 분~수 시간 소요. 임의 재실행 전 유저에게 확인.
- **"논문 작성 시간 부족"을 blocker로 취급하지 말 것**: writing bandwidth는 LLM 지원으로 대체 가능 (단, citation/novelty/이론 framing 한계는 별도 명시).
- **투고 마감 인지**: ICIS 2026 마감이 임박한 시점에는 HICSS 2027 우선 검토를 제안.

## 자주 쓰는 진입점
- 새로운 분석 추가: `top_tier/src/stepXX_*.py` 신설 → `config.py` import → 출력은 규약대로
- 논문 본문 수정: `top_tier/paper_draft/0X_*.md`
- 지도 미팅 자료: `top_tier/advisor_meeting/`
- 외부 데이터 갱신: `top_tier/run_external_refresh.sh`

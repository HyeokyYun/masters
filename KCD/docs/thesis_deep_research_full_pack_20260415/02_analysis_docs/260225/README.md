# 260225 — 개별미팅 피드백 반영

**목적**: 260225 개별미팅 녹취록을 바탕으로 논문 스토리라인·액션아이템 정리 및 후속 작업 진행.

---

## 폴더 구조

```
260225/
├── README.md
├── run_all_steps.py                    # 전체 실행
├── requirements.txt
├── 01_summary_stats/
│   └── run_cluster_summary_statistics.py
├── 02_multinomial_logit/
│   └── run_multinomial_logit.py
├── 03_regression_30w/
│   └── run_regression_30w_only.py
├── outputs/
│   └── tables/                         # outcome4_summary_*, multinomial_logit_*, df_*.csv
└── docs/
    ├── 260225_개별미팅_녹취록_및_액션아이템.md
    ├── 260225_개별미팅_전체녹취록.md
    └── 260225_액션아이템_실행결과_요약.md
```

## 실행 방법

```bash
cd 26-1
python -m venv .venv && source .venv/bin/activate
pip install -r 260225/requirements.txt
python 260225/run_all_steps.py
```

---

## 핵심 피드백 요약

1. **클러스터링**은 논문의 좋은 한 부분이지만, **회귀분석(원인 규명)** 이 반드시 포함되어야 함.
2. **Multinomial Logit** 도입: DUX, DUY, Stable, Decline 3~4개 카테고리로 "어떤 변수가 성공/실패를 견인하는지" 규명.
3. **X변수 추출**: 시계열에서 의미 있는 변수(신규고객비율 30주 평균, 업력, 업종 등)를 정의.
4. **Summary Statistics** 표를 회귀분석 **앞에** 먼저 제시 → 클러스터 간 차이가 큰 변수를 X로 활용.
5. **목차**: 서론 → 하이브리드 제안 → 클러스터별 통계·회귀 → 30주 예측.

---

## Action Item (우선순위)

1. **클러스터별 Summary Statistics 표** 작성
2. **Multinomial Logit** 세팅 (DUX/DUY/Stable/Decline, X변수)
3. 논문 목차 확정 및 초안 작성

---

## 참고 경로

- 기존 회귀·Event Study·Ablation: `../260223/`
- 클러스터·UDX 라벨: `../260204/`, `../260204_gem/`

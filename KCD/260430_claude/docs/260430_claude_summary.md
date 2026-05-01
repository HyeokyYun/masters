# 260430_claude 종합 요약 (한 페이지)

## 한 줄 결론

**시즈널리티(feature/target window를 같은 캘린더 월로 정렬)를 통제하면,
미팅에서 인정된 유일한 아카데믹 contribution(베이스라인 + 클러스터 +
체인지 포인트가 G/S/D 분류를 향상시킴)이 평균 +0.002 macro-F1로 거의
사라진다 — 7개 panel 중 1개만 5% 유의.**

## 진행 단계 / 산출물

| 단계 | 스크립트 | 산출물 |
| --- | --- | --- |
| 01 | `src/step01_build_seasonal_panels.py` | 80개 시즌 정렬 패널 (`outputs/tables/panels/`), `panel_summary.csv` |
| 02 | `src/step02_relabel_gsd_calendar.py` | 80개 캘린더 정렬 라벨 (`outputs/tables/labels/`), `label_distribution.csv` |
| 03 | `src/step03_extract_features.py` | 80개 피처 매트릭스 (`outputs/tables/features/`) |
| 04 | `src/step04_evaluate_seasonal_baseline.py` | RF + LightGBM 시즌 평가 (`seasonal_results_long.csv`, `seasonal_results_summary.csv`), 12개 heatmap, 시작연도 비교 그림 |
| 05 | `src/step05_train_main_model.py` | 7개 panel × A/B/C/D 비교 (`main_model_compare.csv`), paired t-test (`main_model_paired_AvD.csv`), 막대 그래프 |

## 핵심 수치 (RF, target_offset=1)

- 시즌 정렬 후 macro-F1 분포: **0.43 ~ 0.54** (시작월에 따라).
- 시작월 효과 진폭(0.10) ≫ 윈도우 길이 효과(0.02) → 시즈널리티가 분류
  난이도를 좌우.
- 2021 시작 vs 2022 시작 평균 차이는 0.01 미만 → 코로나 잔여 효과는 정확도에
  결정적이지 않음 (미팅에서 교수 우려와 다른 결과).

## 메인 모델 (Step 05) 결과

| panel | A → D | Δ | p |
| --- | --- | --- | --- |
| sy2021_sm01_w3m_off1 | 0.501 → 0.503 | +0.002 | 0.052 |
| sy2021_sm03_w3m_off1 | 0.495 → 0.499 | +0.003 | 0.258 |
| sy2021_sm05_w3m_off1 | 0.488 → 0.488 | +0.001 | 0.787 |
| sy2021_sm09_w3m_off1 | 0.510 → 0.510 | +0.000 | 0.778 |
| sy2022_sm01_w3m_off1 | 0.514 → 0.516 | +0.002 | 0.356 |
| **sy2022_sm03_w3m_off1** | **0.468 → 0.474** | **+0.006** | **0.026** |
| sy2022_sm05_w3m_off1 | 0.518 → 0.519 | +0.001 | 0.511 |

평균 Δ = +0.0022. 유의한 향상은 라벨이 가장 편중된 1개 panel뿐.

## 미팅 후속 의사결정 필요

논문 1번 contribution framing을 다음 중 어느 쪽으로 갈지 다음 미팅에서
교수와 결정 필요 (자세한 논거는 `260430_claude_main_model_results.md` §4):

a. **조건부 contribution**: 라벨 분포 편중 시즌에서만 cluster+CP가 의미.
b. **Trajectory 해석 강조**: 정량 향상보다 정성적 trajectory 분리 가치.
c. **시즈널 confound 노출 자체를 메인**: legacy 결과를 비판적으로 재현.

미팅에서 격리한 아래 항목은 본 폴더 범위 밖 (이전 의사결정 그대로):

- LEVI / 도시경제 활력 지수 → future work / journal 확장.
- EWS 조기 쇠퇴 경보 → 보류 (아카데믹 앵글 부족).
- 외부 공공 데이터 5종 추가 → 보강용으로 분리.
- 5월 8일 학과 지도 커미티 제출 → 행정 작업.

## 재현 명령

```bash
cd /home/hyeoky98/kcd
python 260430_claude/src/step01_build_seasonal_panels.py
python 260430_claude/src/step02_relabel_gsd_calendar.py
python 260430_claude/src/step03_extract_features.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step04_evaluate_seasonal_baseline.py
PYTHONUNBUFFERED=1 python -u 260430_claude/src/step05_train_main_model.py
```

총 wall clock: 약 25–35분 (CPU 8코어 가정, step04가 가장 김).

## 참조

- 미팅 전사: `thesis/meeting_stt/260430_personal_meeting.txt`
- 설계 문서: `260430_claude/docs/260430_claude_design.md`
- 시즌 결과 상세: `260430_claude/docs/260430_claude_rolling_results.md`
- 메인 모델 결과 상세: `260430_claude/docs/260430_claude_main_model_results.md`

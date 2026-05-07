# 논문 방향성 의견 (Rolling 결과를 본 후)

> 본 문서는 본 폴더(260430_claude) 결과를 근거로 한 **명시적 권고**다.
> 03_discussion_points.md의 framing 옵션 (a)/(b)/(c)에 대한 결정을 미팅에서
> 받기 위해, 어떤 입장이 가장 방어 가능한지 입장을 잡는 데 쓴다.

## 한 줄 권고

**Option C(시즈널 confound 노출)를 메인으로 + Option A(조건부 hybrid)를
보조로 결합**. v5_thesis_final이 이미 이 방향이고, 본 폴더 결과가 이 방향을
경험적으로 정당화한다.

## 왜 C를 메인으로 잡아야 하는가 — 3가지 이유

### 1. 가장 정직하고 가장 일반화 가능한 결과

본 분석의 가장 큰 발견은 **시작월 진폭(0.0682) ≫ 윈도우/연도 진폭(0.014/0.011)**
이라는 것이다. 즉, 같은 데이터·같은 모델로도 **라벨링 시점만 바꾸면 분류
난이도가 0.10 폭으로 흔들린다**. 이건 KCD 데이터에 한정된 발견이 아니라
**라이프사이클/이탈 예측 문헌 전반에 적용되는 방법론적 경고**다. 라이프사이클
예측 논문에서 라벨 구간을 시즈널리티 기준으로 정렬하지 않은 사례는 다수 존재.

### 2. Hybrid의 추가 contribution이 사실상 없다 (정직한 negative)

- 시즌 정렬 후 D−A 평균 +0.0022 macro-F1, 7개 panel 중 5% 유의는 1개뿐.
- top_tier 시절의 D ≫ A by ~0.05는 **시즌 confound 위에서 성립한 결과로
  해석**됨.
- 이걸 그대로 "hybrid가 좋다"로 가져가면 외적 타당성 위협이 너무 크다.
  심사위원이 "왜 시즌 통제 안 했나"를 물으면 답변이 무너진다.

### 3. C는 v5_thesis_final 구조와 정합 + 새 본문 골격이 이미 잡혀 있음

CLAUDE.md 명시: v5는 seasonal calendar alignment를 "main methodological
contribution"으로, hybrid를 "conditional finding"으로 demote. 본 폴더 결과가
정확히 이 framing의 실증 근거다. 즉, **이미 그쪽으로 글이 흘러가고 있고,
본 폴더가 그 골격을 채우는 자료다.**

## 그럼 A는 어디에 쓰는가 — 보조 contribution

A를 *완전히* 버릴 필요는 없다. 본 폴더의 결과 안에는 **"라벨 분포가 편중된
시즌 panel(`sy2022_sm03` Stable 75% 편중)에서만 hybrid가 살아남는다"**는
구체적 발견이 있다. 이걸 **§5.5.2 또는 §5.6의 보조 결과**로 다음과 같이
배치하면 좋다:

> "시즌 정렬을 강제하면 cluster + change-point의 추가 정보량은 평균적으로
> 사라지지만(평균 +0.002 macro-F1), 라벨 분포가 한 클래스로 편중된 시즌
> panel에서는 보조 신호로 살아남는다. 즉 hybrid representation은 **데이터
> 전체에 일반화되는 contribution이 아니라, 특정 분포 조건에서만 작동하는
> 조건부 contribution**이다."

이 narrative는:
- 기존 hybrid 작업(top_tier)을 완전히 폐기하지 않음 → 1년치 작업이 남음
- "negative result만 있는 논문"이라는 약점을 피함
- 심사위원이 "hybrid 결과는 어디갔냐"고 물으면 §5.5.2를 가리킬 수 있음

## 본문 골격 권고 (v5_thesis_final 기준)

| 챕터 | 현재 | 권고 |
| --- | --- | --- |
| Ch1 (서론) | 라이프사이클 예측 동기 | + "기존 문헌이 시즌 통제 없이 마지막 N주 라벨을 사용해 왔다"는 motivation 한 단락 추가 |
| Ch4 (방법론) | seasonal calendar alignment | **유지**. 본 폴더 §1 인벤토리(146 panel)와 결합 |
| Ch5.5.1 (메인) | seasonal alignment 결과 | **유지**. 진폭 표(0.068 vs 0.014 vs 0.011)가 main figure 후보 |
| Ch5.5.2 (보조) | 확장 윈도우 placeholder | **+ hybrid 조건부 결과**: 80 panel D−A delta heatmap + 라벨 편중 panel만 향상되는 패턴 |
| Ch5.6/5.7 | 요약 | 시즌 정렬을 통제했을 때 legacy "마지막 30주" 결과가 어떻게 재해석되는지 한 페이지 |
| Ch6 (논의) | discussion | **negative finding을 contribution으로** 적극적으로 framing |
| Ch7 (future work) | LEVI/EWS/외부데이터 | 04-30 결정대로 1–2 페이지 future work로 |

## 미팅에서 그대로 말할 수 있는 형태

> "교수님, 이 방향으로 가는 게 맞을 것 같습니다. **시즌 정렬을 메인 contribution
> 으로**, hybrid는 데이터 전체가 아니라 라벨 편중 panel에서만 살아남는 **조건부
> 보조 결과로** 배치하겠습니다. 그러면 (1) 04-30 미팅에서 인정해 주신 hybrid의
> 가치는 §5.5.2의 조건부 contribution으로 살아남고, (2) 메인 contribution은
> 더 일반화 가능하고 정직한 방법론적 발견이 됩니다. 04-30 미팅 톤에서 v5로 가는
> 차이를 한 페이지 diff로 만들어 다음 주에 가져오겠습니다."

## 베뉴 전략 함의

CLAUDE.md 매핑에 따르면:

- **HICSS (가장 적합)**: "decision-support / digital trace / public-value analytics"
  framing. 본 폴더의 시즌 confound 노출은 digital trace에서 **labeling
  protocol의 표준화 부재**라는 일반적 issue로 framing 가능. 매우 잘 맞음.
- **DSS (가능)**: artifact 평가 + calibration이 있어야 함. 본 폴더는 artifact
  평가는 있지만 calibration이 없음 → 추가 작업 필요.
- **I&M (가능)**: managerial / digital trace framing. 본 폴더 그대로 가져갈 수 있음.
- **SBE (가능)**: LEVI 보강 후. 본 폴더 범위 밖이지만 future work에서 가능.
- **ICIS (위험)**: IS theory가 약함. 시즌 confound만으로는 IS theory 채우기 어려움.
- **MISQ/ISR/JMIS (현실적이지 않음)**: 이론 추상화 부족.

→ **HICSS를 우선 타깃**으로 두고, 거절되면 DSS / I&M으로 가는 시퀀스가
자연스럽다. 본 폴더의 시즌 confound 발견은 이 시퀀스 어디서도 제1 contribution
으로 작동한다.

## 미팅 후 1주 안에 만들 산출물 (이 framing을 지지하기 위해)

1. **80 panel D−A delta heatmap** (`step05` 확장 실행).
   - X축: start_month, Y축: window_months, 색: D−A delta.
   - "어디서 hybrid가 살아남는가"를 한 그림으로 노출.
2. **legacy `top_tier` 재현 표**: 동일 점포로 마지막-30주 라벨 vs 시즌 정렬
   라벨의 macro-F1 비교. "시즌 confound가 ~0.05를 인위적으로 만들고 있었음"
   을 한 표로 증명.
3. **v5_thesis_final §5.5.2 placeholder 채우기** (확장 윈도우 + 조건부 hybrid).
4. **진폭 분산 분해(ANOVA)**: 시작월 / 윈도우 / 연도 / 점포 분산이 macro-F1
   변동의 몇 %씩을 설명하는지. 본 폴더의 "5배 차이" 수치를 통계적으로 보강.

## 위험 요소 — 미리 답변 준비할 것

- "조건부 contribution이 너무 좁다"는 지적: §5.5.2가 단일 panel 사례가 아니라
  **80 panel × 라벨 편중 vs 균형 비교**로 패턴화되어야 설득력. → 산출물 1번이
  이 답변의 자료.
- "negative result로만 가도 되나": 메인 contribution은 **negative가 아니라
  positive methodological**(=시즌 정렬이라는 새 표준 절차의 실증). hybrid의
  negative는 그 결과를 입증하는 부수적 증거.
- "그럼 top_tier 작업은 다 버리는 거냐": 아니다. §5.5.2 + §5.6의 재현 표 +
  §6 discussion에서 모두 인용. 1년치 작업이 paper 트랙 / future work로
  계속 살아남음.

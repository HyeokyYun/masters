# Deep Research Prompt

저는 학위논문을 작성하려고 합니다. 주제는 KCD 주별 거래 데이터를 활용한 서울시 외식업 소상공인의 생애주기 진단과 조기 예측입니다.

첨부한 자료들을 바탕으로 학위논문용 outline과 main result 구조를 잡아주세요. 특히 `DEEP_RESEARCH_BRIEF.md`를 최우선 근거 가이드로 사용해 주세요. 원본 실험 폴더 전체는 Deep Research에 없으므로, 해당 brief에 정리된 수치와 해석 제약을 따라 주세요.

## 자료

1. `KCD_FINAL.pdf`
   - 기존 용역보고서/초안 성격의 문서입니다.
   - 핵심 내용: 주별 매출 데이터로 소상공인 생애주기 패턴을 정의하고, DDZ/UUX 같은 trajectory label을 만들며, 20~30주 정보로 조기 진단 가능성을 논의합니다.

2. `개별미팅 26-1.docx`, `개별미팅_25-1학기.docx`, `연구 발표.pdf`
   - 교수님과의 개별 미팅 및 연구 발표 기록입니다.
   - 연구 흐름이 여러 번 바뀌었으므로, 최신 결과와 충돌하는 초기 아이디어는 그대로 main result로 쓰지 말고 비판적으로 정리해주세요.

3. `KER_Extended_Abstract_Final.md`
   - 현재 연구 방향을 요약한 extended abstract입니다.

4. `DEEP_RESEARCH_BRIEF.md`
   - 로컬 실험 폴더의 핵심 결과를 요약한 증거 브리프입니다.
   - 이 파일의 해석 제약을 반드시 반영해주세요.

## 중요한 해석 제약

- 논문의 중심 주장은 "소상공인 생애주기는 단일한 창업→성장→성숙→쇠퇴 곡선이 아니라, 초기 진입 trajectory와 전체 생존 업장의 observed-window 상태를 분리해서 봐야 한다"로 잡고 싶습니다.
- "골든크로스"는 흥미로운 보조 결과일 수 있지만, main result로 과장하지 마세요.
- "성장 업장은 변동성이 높다"라고 단정하지 마세요. 최신 분석에서는 추세조정 변동성 기준으로 Growth의 변동성이 오히려 낮거나, 적어도 기존 CV 해석보다 조심해야 합니다.
- K-shape를 혁신적인 핵심 방법론으로 과장하지 마세요. 비교 결과상 안정성이 낮은 부분이 있으므로, trajectory/state labeling을 위한 보조적 방법론으로 조심스럽게 서술하세요.
- 예측 결과에서는 cluster 자체보다 trend/volatility, customer behavior, local context feature block의 기여가 더 중요해 보입니다.

## 원하는 결과물

1. 학위논문 전체 outline
   - Chapter 1 Introduction부터 Conclusion까지.
   - 각 장의 핵심 질문, 들어갈 결과, 들어갈 표/그림 제안 포함.

2. Main result 3개 선정
   - Result 1: 초기 trajectory와 observed-window 상태를 분리해야 한다는 결과.
   - Result 2: 업력 구간별 driver가 다르며 trend, MDD, 신규 고객 비율이 핵심이라는 결과.
   - Result 3: 초기 정보 기반 예측에서 level-only보다 trend/volatility, customer behavior, local context가 성능을 올린다는 결과.
   - 위 방향이 부적절하면 근거를 들어 수정 제안.

3. Main figure 구성
   - Figure 1: 초기 trajectory 패턴 + 전체 업장 업력별 Growth/Stable/Decline 비중을 합친 composite figure.
   - Figure 2: 업력 구간별 핵심 driver, 예: trend/MDD/nc_rate coefficient 또는 importance summary.
   - Figure 3: 예측 feature ablation, 예: level only → trend/volatility → customer behavior → local context → cluster.
   - 보조/appendix figure로 보낼 것들도 구분.

4. 논문 제목 후보 5개
   - 영어 제목과 한국어 제목 둘 다 제안.

5. Abstract 초안
   - 250~350 words 영어 abstract.
   - 지나친 인과 주장 없이 empirical design과 main findings 중심으로 작성.

6. 작성 전략
   - 어떤 결과를 본문에 넣고, 어떤 결과를 appendix로 보내야 하는지.
   - 기존 `KCD_FINAL.pdf`에서 가져올 부분과 최신 분석으로 교체할 부분.
   - 교수님께 보여줄 1페이지 요약 구조.


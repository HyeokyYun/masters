# 제2장 선행연구

본 장은 본 연구의 위치를 네 갈래 문헌 안에서 정리한다. (1) 소상공인 라이프
사이클과 폐업 결정요인, (2) 거래 데이터 기반 점포 진단, (3) 시계열 분류와
representation learning, (4) 시즌 통제와 cross-validation robustness check.
각 갈래의 한계와 본 연구가 채우는 지점을 명시한다.

## 2.1 소상공인 라이프사이클과 폐업 결정요인

조직 라이프사이클 이론은 기업의 진화 단계를 출생, 성장, 성숙, 쇠퇴로
구분하고(Greiner, 1972; Quinn & Cameron, 1983), 각 단계에서의 자원·역량·
구조 변화를 다룬다. 이 이론은 대기업·중견기업의 사례 연구에서 확인됐으며
(Miller & Friesen, 1984), 이후 자영업·소상공인 영역으로도 확장됐다
(Davidsson & Honig, 2003). 다만 소상공인의 경우 폐업률이 높고(개업 후
5 년 내 폐업 50% 이상; 통계청, 2023) 진입과 종료가 동시에 일어나, 단계
구분 자체가 이산적 분류보다 연속적 상태 변동으로 다뤄질 필요가 있다.

거시 결정요인으로는 거시경제 충격(Carree & Thurik, 2010), 지역 인구·소득
구조(Audretsch & Lehmann, 2005), 업종 경쟁 밀도(Stinchcombe, 1965) 가
주요하게 다뤄졌고, 미시 결정요인으로는 창업자 인적자본(Gimeno et al., 1997),
초기 자금 규모(Cassar, 2004), 거래 채널 다변화(Lee & Park, 2023) 가 보고
되었다. 한국 외식업 맥락에서는 코로나19 충격(이수진·박지영, 2022)과 배달
플랫폼 도입(김재현·최영수, 2023)이 중요한 외생 요인으로 다뤄졌다.

본 연구는 이 문헌의 G/S/D 3-class 라벨 형식을 따르되, 라벨을 점포의 종료
시점이 아니라 관측 가능한 매출 추세의 시즌 정렬된 기울기로 정의한다는
점에서 기존 폐업 이분법 분석과 다르다.

## 2.2 거래 데이터 기반 점포 진단

POS, 카드 결제, 모바일 결제 등 고빈도 거래 데이터는 행정 통계가 보지 못하는
점포 단위의 동태를 거의 실시간으로 보여준다. 미국에서는 신용카드 매출 데이터
를 활용한 지역 경제 nowcasting (Aladangady et al., 2021) 과 점포 단위 수익·
고용 분석(Mian & Sufi, 2014; Granja et al., 2022) 이 활발하다. 한국에서는
KIS·서울신용보증재단·KCD 가 카드 매출 데이터를 점포 단위로 제공하기
시작하면서 자영업자 신용평가(이호철, 2021), 상권 분석(서울신용보증재단,
2023), 폐업 예측(김민·박상호, 2023) 연구가 등장했다.

이 문헌의 공통적 한계는 라벨 정의의 임의성이다. "마지막 N 주", "전체 기간
기울기", "관측 종료 시점 매출 비교" 등 라벨 시점 선택이 연구자마다 다르고,
시즌·휴가·이벤트 효과가 라벨 안에 흡수되는 정도가 측정되지 않는다. 본
연구는 이 한계를 직접 다룬다.

## 2.3 시계열 분류와 Representation Learning

매출 시계열을 분류 입력으로 사용할 때, 단순 통계량(평균, 분산, 기울기)에
더해 형태 기반 representation 을 추가하면 분류 정확도가 개선될 수 있다는
보고가 다수 있다. KMeans / K-Shape 기반 클러스터(Paparrizos & Gravano, 2015),
DTW 기반 거리(Ratanamahatana & Keogh, 2005), 변곡점(change-point) 추출
(Truong et al., 2020), Shapelet 추출(Ye & Keogh, 2009) 등이 자주 쓰인다.
딥러닝 영역에서는 1D-CNN, LSTM, Transformer 가 활용되지만(Fawaz et al.,
2019), 점포 단위 데이터처럼 시퀀스 길이가 짧고(30 주 이하) 점포 수가 많은
경우 트리 기반 모델(RandomForest, LightGBM, XGBoost)에 통계 피처를 결합
하는 방식이 종종 더 강한 baseline 을 제공한다.

본 연구가 비교 대상으로 삼는 hybrid representation 은 KMeans 클러스터
one-hot + change-point 피처를 baseline 통계 피처에 결합하는 형식으로
(`top_tier/src/step10_hybrid_prediction.py`), 위 문헌의 표준적 조합이다.
이 representation 이 시즌 통제 라벨에서도 향상을 제공하는지가 RQ3 의 직접
답이다.

## 2.4 시즌 통제와 Cross-Validation Robustness

시계열 예측 / 분류에서의 시즌 통제는 forecasting 문헌(Hyndman &
Athanasopoulos, 2021)과 OOS 검증 문헌(Bergmeir & Benítez, 2012; Cerqueira
et al., 2020) 에서 반복적으로 강조됐다. 핵심 원리는 train / test 분할이
시간 / 시즌 정보를 누설하지 않아야 한다는 것이다. 점포 단위 데이터에서는
train / test 가 점포 ID 로 분할되기 때문에 정보 누설은 적지만, 라벨이 항상
같은 캘린더 시점에 묶여 있다면 학습된 모델은 시즌 효과를 점포 특성으로
오해할 수 있다.

이 문제에 대한 표준적 해법은 (a) 라벨 시점을 시즌별로 분리하거나(seasonally
stratified labeling), (b) 라벨/피처 윈도우의 시즌을 일치시키는 rolling
-window 정렬이다. 후자는 시계열 forecasting 에서 sliding-window cross
-validation 으로 잘 알려져 있지만, 점포 단위 라이프사이클 분류에 적용된
사례는 드물다.

본 연구의 시즌 정렬 rolling-window 설계는 이 표준을 점포 단위 G/S/D 분류에
직접 적용한 형태이며, 80 개 이상 specification 에서 시즌 효과의 진폭과
hybrid representation 의 조건부 향상을 정량화한다.

## 2.5 본 연구의 위치

본 연구는 위 네 갈래에 걸쳐 다음과 같이 자리한다.

- **라이프사이클 이론 측면**: G/S/D 3-class 라벨로 폐업 이분법을 확장.
- **거래 데이터 진단 측면**: 카드 매출 라벨 정의의 시즌 confound 를 정량
  폭로.
- **시계열 representation 측면**: hybrid representation 의 조건부
  contribution 발견.
- **시즌 통제 robustness 측면**: rolling-window 정렬을 점포 분류로 도입.

이 네 갈래의 교차점에 본 연구의 두 contribution(시즌 robustness 방법론 +
hybrid representation 조건부 향상) 이 위치한다.

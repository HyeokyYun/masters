# 초록

## 국문 초록

소상공인 점포의 성장과 쇠퇴는 지역경제와 금융지원 정책에서 중요한 관찰 대상이지만, 기존 행정통계는 점포 단위의 동태적 변화를 조기에 포착하는 데 한계가 있다. 본 연구는 서울시 외식업 점포의 주간 카드거래 데이터를 활용하여, 영업 초기 거래 패턴이 이후 점포의 생애주기 상태를 예측할 수 있는지 분석한다. 구체적으로 점포의 이후 상태를 Growth, Stable, Decline으로 구분하고, 초기 관측 구간에서 추출한 매출, 고객, 거래, 변동성, 추세 관련 feature가 이후 상태 분류에 어느 정도의 정보를 제공하는지 검토한다.

본 연구의 핵심 방법론적 쟁점은 계절성이다. 초기 구간과 후기 구간을 단순히 고정된 위치에서 비교하면, 특정 월 또는 계절의 소비 패턴이 생애주기 변화로 오인될 가능성이 있다. 이를 보완하기 위해 본 연구는 같은 월에 시작하는 feature window와 target window를 구성하는 rolling-window 검증을 수행한다. 예컨대 1월부터 3월까지의 초기 패턴은 다음 해 1월부터 3월까지의 상태와 비교하고, 2월부터 4월까지의 패턴은 다음 해 2월부터 4월까지의 상태와 비교한다. 이 설계는 생애주기 예측 신호가 단순한 계절 효과인지 여부를 검토하기 위한 robustness check로 사용된다.

분석 결과, 초기 거래 패턴은 이후 점포 상태 예측에 의미 있는 정보를 제공한다. 기존 full-window 예측에서는 trajectory 및 change-point 정보를 결합한 hybrid representation이 기본 feature 대비 성능을 개선하였다. 또한 계절성 보정 rolling-window 검증에서도 예측 신호는 완전히 사라지지 않았으며, 최고 성능 specification은 Macro-F1 0.509, AUC 0.722, Decline recall 0.663을 보였다. 이는 카드거래 기반 조기 신호가 단순히 특정 계절 비교의 산물이 아니라, 점포의 이후 생애주기 상태와 관련된 정보를 포함할 가능성을 시사한다.

본 연구는 세 가지 측면에서 기여한다. 첫째, 고빈도 카드거래 데이터를 활용하여 점포 단위 생애주기 예측 문제를 실증적으로 구성한다. 둘째, 관측 초기 기간의 길이와 하락 점포 포착 성능의 관계를 제시하여 조기 예측의 실무적 trade-off를 보인다. 셋째, 계절성 보정 rolling-window 검증을 통해 기존 late-window outcome 정의의 취약성을 보완하고, 예측 결과의 방법론적 신뢰성을 강화한다. LEVI, Golden Cross, EWS와 같은 확장 분석은 본 논문에서 후속 연구 또는 응용 가능성으로 논의한다.

주요어: 소상공인, 카드거래 데이터, 생애주기 예측, 조기경보, 계절성, 외식업

## English Abstract

Small-business growth and decline are important signals for local economic monitoring and policy support, yet conventional administrative statistics often fail to capture store-level dynamics at an early stage. This thesis examines whether early transaction patterns can predict the subsequent lifecycle state of food-service stores in Seoul. Using weekly card-transaction data, stores are classified into Growth, Stable, and Decline outcomes, and early-window features are used to predict later lifecycle states.

A central methodological issue is seasonality. If early and late windows are compared at fixed positions in the panel, calendar-specific consumption patterns may be confounded with lifecycle dynamics. To address this concern, this study implements a seasonality-corrected rolling-window validation in which feature and target windows are matched by calendar month across years. The results show that early transaction patterns remain informative even after this correction, although performance varies across start months and window lengths.

The thesis contributes to the literature by formulating store-level lifecycle prediction with high-frequency transaction data, by documenting the relationship between observation-window length and decline detection, and by providing a seasonality-aware robustness check for early-warning analysis. Extensions such as LEVI, Golden Cross, and EWS are discussed as future research and application pathways rather than as the main contribution of the thesis.


"""
lstm_v3.py 실행 후 gemini 추천 방향

1) autoencoder.fit(X_train, X_train): 입력(X)을 넣고 똑같은 입력(X)을 맞히라고 시킵니다. "예측"이 아니라 "복원"이 목적이기 때문입니다.

2)LATENT_DIM = 32: 12주간의 매출 흐름을 32개의 숫자로 요약합니다. 이 32개 숫자 안에는 "상승세", "변동성", "계절성" 같은 정보가 녹아들어 가게 됩니다.

3) 결과물: lstm_extracted_features.csv 파일이 생성됩니다.
다음 단계: 기존 XGBoost 모델의 입력 데이터에 이 CSV를 merge해서 컬럼 32개를 추가한 뒤 돌려보세요. F1-score가 오를 가능성이 매우 높습니다.

tmux attach -t lstm_v2_update
"""


import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed, Input
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.callbacks import EarlyStopping


# GPU 설정 (기존과 동일)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
USE_GPU_ID = 1 

gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        tf.config.set_visible_devices([gpus[USE_GPU_ID]], 'GPU')
        tf.config.experimental.set_memory_growth(gpus[USE_GPU_ID], True)
        print(f"✅ GPU {USE_GPU_ID}번 사용 설정 완료")
    except RuntimeError as e:
        print(e)

# =========================================================
# 1. 데이터 준비 (로그 변환 유지)
# =========================================================
print("[1] 데이터 로드 및 전처리...")
weekly_df = pd.read_parquet('../original_data/weekly_processed.parquet')

# 로그 변환 (이건 효과가 좋았으니 유지)
weekly_df['sales_card'] = np.log1p(weekly_df['sales_card'])

# 각 매장별로 정규화 (MinMax) 진행을 위해 그룹핑
# Autoencoder는 패턴의 '형태'가 중요하므로 매장별 스케일링이 유리함
scaler = MinMaxScaler()
# 전체 데이터를 한 번에 스케일링 (단순화를 위해)
weekly_df['sales_scaled'] = scaler.fit_transform(weekly_df[['sales_card']])

# 시퀀스 생성 함수 (Target이 자기 자신임)
def create_autoencoder_dataset(data, seq_len):
    X = []
    ids = []
    
    public_ids = data['public_id'].unique()
    
    for pid in public_ids:
        store_data = data[data['public_id'] == pid].sort_values('day_after1')
        values = store_data['sales_scaled'].values
        
        if len(values) < seq_len:
            continue
            
        # 가장 최근 패턴 하나만 추출 (XGBoost에 넣을 현재 상태)
        # 연구 목적에 따라 슬라이딩 윈도우로 여러 개를 뽑을 수도 있음
        # 여기서는 '각 매장의 대표 패턴'을 학습하기 위해 전체 구간 사용
        for i in range(len(values) - seq_len + 1):
            X.append(values[i : i + seq_len])
            ids.append(pid)
            
    return np.array(X), np.array(ids)

SEQUENCE_LENGTH = 12  # 12주 패턴을 압축
LATENT_DIM = 32       # 32개의 숫자로 요약 (Embedding Size)

X_train, store_ids = create_autoencoder_dataset(weekly_df, SEQUENCE_LENGTH)

# LSTM 입력 형태: (samples, timesteps, features)
X_train = X_train.reshape(X_train.shape[0], SEQUENCE_LENGTH, 1)

print(f"학습 데이터 형태: {X_train.shape}")
print(f" - 샘플 수: {len(X_train)}")
print(f" - 시퀀스 길이: {SEQUENCE_LENGTH}")

# =========================================================
# 2. LSTM Autoencoder 모델 구성
# =========================================================
print("\n[2] Autoencoder 모델 구축...")

# 입력 레이어
inputs = Input(shape=(SEQUENCE_LENGTH, 1))

# [Encoder] 정보를 압축하는 단계
encoded = LSTM(64, activation='relu', return_sequences=True)(inputs)
encoded = LSTM(LATENT_DIM, activation='relu', return_sequences=False)(encoded) 
# encoded -> 이 친구가 바로 우리가 원하는 '특징 벡터'입니다!

# [Decoder] 압축된 정보로 다시 원래 데이터를 복원하는 단계
decoded = RepeatVector(SEQUENCE_LENGTH)(encoded)
decoded = LSTM(64, activation='relu', return_sequences=True)(decoded)
decoded = TimeDistributed(Dense(1))(decoded)

# 전체 모델 (학습용)
autoencoder = Model(inputs, decoded)
autoencoder.compile(optimizer='adam', loss='mse')

# Encoder 모델 (추출용)
encoder_model = Model(inputs, encoded)

autoencoder.summary()

# =========================================================
# 3. 학습 (Reconstruction Learning)
# =========================================================
print("\n[3] 특징 학습 시작 (Input == Target)...")

early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)

# X_train을 입력과 정답 모두에 넣습니다. (자기 자신을 복원하라는 뜻)
history = autoencoder.fit(
    X_train, X_train,
    epochs=50,
    batch_size=256,
    validation_split=0.2,
    callbacks=[early_stop],
    verbose=1
)

# =========================================================
# 4. 특징 추출 및 저장
# =========================================================
print("\n[4] 학습된 특징(Embeddings) 추출 중...")

# 전체 데이터에 대해 특징 벡터 추출
latent_features = encoder_model.predict(X_train)

print(f"추출된 특징 형태: {latent_features.shape}")
# 예: (샘플수, 32)

# 데이터프레임으로 변환
col_names = [f'lstm_feat_{i}' for i in range(LATENT_DIM)]
features_df = pd.DataFrame(latent_features, columns=col_names)
features_df['public_id'] = store_ids

# 매장별로 평균 특징 벡터 계산 (한 매장에서 여러 시퀀스가 나왔으므로)
# "이 매장은 대체로 이런 시계열 특성을 가진다"라고 요약
final_features = features_df.groupby('public_id')[col_names].mean().reset_index()

print(f"최종 매장별 특징 데이터: {final_features.shape}")

# 저장
save_path = '../result_csv/lstm_extracted_features.csv'
final_features.to_csv(save_path, index=False)
print(f"✅ 저장 완료: {save_path}")
print("이제 이 파일을 XGBoost의 입력 변수(feature)로 사용하세요.")
"""
LSTM Experiment for Sales Prediction (Improved Version)
- 다중 feature 사용 (sales_card, sales_ratio, 이동평균, 트렌드 등)
- 시간 순서를 고려한 데이터 분할
- 업장별 정규화
- Bidirectional LSTM + Attention 메커니즘
- 시계열 특성 추가

개선 사항:
1. 다중 feature 사용으로 정보량 증가
2. 시간 순서 고려 분할로 데이터 누수 방지
3. 업장별 정규화로 스케일 차이 해결
4. Bidirectional LSTM으로 양방향 패턴 학습
5. 시계열 특성 추가 (이동평균, 트렌드 등)

gpt5.2

tmux attach -t lstm_v3

"""

import os
import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# TensorFlow 경고 메시지 억제
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# GPU 선택
USE_GPU_ID = 2

# TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (
        LSTM, Dense, Dropout, Bidirectional, 
        Input, Concatenate, Multiply, Add
    )
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    print("TensorFlow version:", tf.__version__)
    tf.get_logger().setLevel('ERROR')
except ImportError:
    print("ERROR: TensorFlow가 설치되지 않았습니다.")
    sys.exit(1)

# GPU 설정
print("\nGPU 설정 확인:")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"  GPU 사용 가능: {len(gpus)}개")
    if USE_GPU_ID < len(gpus):
        tf.config.set_visible_devices([gpus[USE_GPU_ID]], 'GPU')
        print(f"  ✅ GPU {USE_GPU_ID}번 사용")
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
    except:
        pass
else:
    print("  GPU 사용 불가 - CPU 사용")

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
os.makedirs('results', exist_ok=True)

print("=" * 80)
print("LSTM Experiment for Sales Prediction (Improved Version)")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

weekly_df = pd.read_parquet('../original_data/weekly_processed.parquet')
cluster_labels = pd.read_csv('../result_csv/cluster_labels.csv')

print(f"weekly_processed.parquet: {weekly_df.shape}")
print(f"cluster_labels: {cluster_labels.shape}")

# 클러스터 레이블 병합
weekly_df = weekly_df.merge(cluster_labels, on='public_id', how='inner')
print(f"병합 후 데이터: {weekly_df.shape}")

# day_after1=0 제외
weekly_df = weekly_df[weekly_df['day_after1'] != 0]

# 시계열 길이 필터링
min_weeks = 50
store_counts = weekly_df.groupby('public_id').size()
valid_stores = store_counts[store_counts >= min_weeks].index
weekly_df = weekly_df[weekly_df['public_id'].isin(valid_stores)]

print(f"최소 {min_weeks}주 이상 데이터를 가진 업장 수: {len(valid_stores)}")

# ============================================================================
# 2. 시계열 특성 생성 함수
# ============================================================================
def create_time_features(data):
    """
    시계열 특성 생성:
    - 이동평균 (7일, 14일, 30일)
    - 트렌드 (선형 추세)
    - 변동성 (표준편차)
    """
    data = data.copy()
    data = data.sort_values('day_after1')
    
    # 이동평균
    data['ma_4'] = data.groupby('public_id')['sales_card'].transform(lambda x: x.rolling(4, min_periods=1).mean())
    data['ma_8'] = data.groupby('public_id')['sales_card'].transform(lambda x: x.rolling(8, min_periods=1).mean())
    data['ma_12'] = data.groupby('public_id')['sales_card'].transform(lambda x: x.rolling(12, min_periods=1).mean())
    
    # 트렌드 (최근 4주 평균 대비 변화율)
    data['trend_4'] = data.groupby('public_id')['sales_card'].transform(
        lambda x: (x.rolling(4, min_periods=1).mean() / x.rolling(8, min_periods=1).mean() - 1).fillna(0)
    )
    
    # 변동성 (최근 4주 표준편차)
    data['volatility_4'] = data.groupby('public_id')['sales_card'].transform(
        lambda x: x.rolling(4, min_periods=1).std().fillna(0)
    )
    
    # lag features
    data['lag_1'] = data.groupby('public_id')['sales_card'].shift(1).fillna(method='bfill')
    data['lag_4'] = data.groupby('public_id')['sales_card'].shift(4).fillna(method='bfill')
    
    # day_after1 정규화 (0-1 범위)
    max_day = data['day_after1'].max()
    data['day_after1_norm'] = data['day_after1'] / max_day
    
    # 결측값 처리
    data = data.fillna(0)
    
    return data

print("\n[2] 시계열 특성 생성 중...")
weekly_df = create_time_features(weekly_df)
print("시계열 특성 생성 완료")

# ============================================================================
# 3. 다중 feature 시퀀스 생성 함수
# ============================================================================
def create_multi_feature_sequences(data, sequence_length, prediction_horizon, use_time_split=True):
    """
    다중 feature를 사용한 시퀀스 생성
    - sales_card: 실제 매출
    - sales_ratio: 매출 비율
    - ma_4, ma_8, ma_12: 이동평균
    - trend_4: 트렌드
    - volatility_4: 변동성
    - day_after1_norm: 정규화된 시간
    """
    X, y, public_ids, day_after1s = [], [], [], []
    public_id_list = data['public_id'].unique()
    
    for pid in public_id_list:
        store_data = data[data['public_id'] == pid].sort_values('day_after1')
        
        if len(store_data) < sequence_length + prediction_horizon:
            continue
        
        # Feature 선택
        features = [
            'sales_card', 'sales_ratio',
            'ma_4', 'ma_8', 'ma_12',
            'trend_4', 'volatility_4',
            'day_after1_norm'
        ]
        
        # Feature 데이터 추출
        feature_data = store_data[features].values
        
        # 시퀀스 생성
        for i in range(len(feature_data) - sequence_length - prediction_horizon + 1):
            X.append(feature_data[i:i+sequence_length])
            y.append(store_data['sales_card'].values[i+sequence_length:i+sequence_length+prediction_horizon])
            public_ids.append(pid)
            day_after1s.append(store_data['day_after1'].values[i+sequence_length])
    
    X = np.array(X)
    y = np.array(y)
    
    # 시간 순서를 고려한 분할을 위한 인덱스
    if use_time_split:
        day_after1s = np.array(day_after1s)
        sorted_idx = np.argsort(day_after1s)
        X = X[sorted_idx]
        y = y[sorted_idx]
        public_ids = np.array(public_ids)[sorted_idx]
    
    return X, y, public_ids

# ============================================================================
# 4. 업장별 정규화 함수
# ============================================================================
def normalize_by_store(X, y, public_ids, feature_idx=0):
    """
    업장별로 정규화 (sales_card 기준)
    feature_idx: 정규화할 feature의 인덱스 (sales_card = 0)
    """
    X_normalized = X.copy()
    y_normalized = y.copy()
    
    unique_stores = np.unique(public_ids)
    store_scalers = {}
    
    for store_id in unique_stores:
        store_mask = public_ids == store_id
        
        # 해당 업장의 sales_card 값 추출
        store_X_sales = X[store_mask][:, :, feature_idx]
        store_y = y[store_mask]
        
        # 전체 값 결합하여 스케일러 생성
        all_values = np.concatenate([store_X_sales.flatten(), store_y.flatten()])
        
        if len(all_values) > 0 and np.std(all_values) > 0:
            scaler = StandardScaler()
            scaler.fit(all_values.reshape(-1, 1))
            store_scalers[store_id] = scaler
            
            # X 정규화 (sales_card만)
            X_normalized[store_mask, :, feature_idx] = scaler.transform(
                store_X_sales.reshape(-1, 1)
            ).reshape(store_X_sales.shape)
            
            # y 정규화
            if len(store_y.shape) == 1:
                y_normalized[store_mask] = scaler.transform(
                    store_y.reshape(-1, 1)
                ).flatten()
            else:
                y_normalized[store_mask] = scaler.transform(
                    store_y.reshape(-1, 1)
                ).reshape(store_y.shape)
    
    return X_normalized, y_normalized, store_scalers

# ============================================================================
# 5. Attention 메커니즘 (간단한 버전)
# ============================================================================
from tensorflow.keras.layers import Dense, Softmax, Multiply, Lambda

def attention_layer(inputs):
    # inputs: (batch, seq_len, hidden)

    score = Dense(64, activation='tanh')(inputs)      # (batch, seq_len, 64)
    score = Dense(1, activation=None)(score)          # (batch, seq_len, 1)

    weights = Softmax(axis=1)(score)                  # (batch, seq_len, 1)

    weighted = Multiply()([inputs, weights])          # (batch, seq_len, hidden)
    context = Lambda(lambda x: tf.reduce_sum(x, axis=1))(weighted)  # (batch, hidden)

    return context, weights

# ============================================================================
# 6. 개선된 LSTM 모델 생성
# ============================================================================
def create_improved_lstm_model(sequence_length, n_features, horizon):
    """
    개선된 LSTM 모델:
    - Bidirectional LSTM
    - Attention 메커니즘
    - 더 깊은 네트워크
    """
    inputs = Input(shape=(sequence_length, n_features))
    
    # Bidirectional LSTM layers
    lstm1 = Bidirectional(LSTM(128, return_sequences=True))(inputs)
    lstm1 = Dropout(0.3)(lstm1)
    
    lstm2 = Bidirectional(LSTM(64, return_sequences=True))(lstm1)
    lstm2 = Dropout(0.3)(lstm2)
    
    # Attention
    attention, attention_weights = attention_layer(lstm2)
    
    # Dense layers
    dense1 = Dense(64, activation='relu')(attention)
    dense1 = Dropout(0.2)(dense1)
    
    dense2 = Dense(32, activation='relu')(dense1)
    dense2 = Dropout(0.1)(dense2)
    
    # Output
    outputs = Dense(horizon, dtype='float32')(dense2)
    
    model = Model(inputs=inputs, outputs=outputs)
    
    return model

# ============================================================================
# 7. 단기 예측 (1-4주)
# ============================================================================
print("\n[7] 단기 예측 모델 학습 (1-4주)...")

sequence_length = 16  # 16주 입력 (기존 12주에서 증가)
prediction_horizons = [1, 2, 4]

short_term_results = []

for horizon in prediction_horizons:
    print(f"\n  [{horizon}주 예측]")
    
    # 시퀀스 생성
    X, y, public_ids = create_multi_feature_sequences(
        weekly_df, sequence_length, horizon, use_time_split=True
    )
    
    if len(X) == 0:
        print(f"    데이터 부족으로 건너뜀")
        continue
    
    print(f"    시퀀스 수: {len(X):,}")
    print(f"    입력 shape: {X.shape}, 출력 shape: {y.shape}")
    print(f"    Feature 수: {X.shape[2]}")
    
    # 업장별 정규화 (sales_card만, feature_idx=0)
    X_normalized, y_normalized, store_scalers = normalize_by_store(
        X, y, public_ids, feature_idx=0
    )
    
    # 나머지 feature들도 정규화 (MinMaxScaler)
    n_features = X.shape[2]
    feature_scalers = []
    
    for feat_idx in range(n_features):
        if feat_idx == 0:  # sales_card는 이미 정규화됨
            feature_scalers.append(None)
            continue
        
        scaler = StandardScaler()
        feat_data = X_normalized[:, :, feat_idx].reshape(-1, 1)
        X_normalized[:, :, feat_idx] = scaler.fit_transform(feat_data).reshape(
            X_normalized[:, :, feat_idx].shape
        )
        feature_scalers.append(scaler)
    
    # 시간 순서를 고려한 분할 (최근 20%를 테스트로)
    split_idx = int(len(X_normalized) * 0.8)
    X_train, X_test = X_normalized[:split_idx], X_normalized[split_idx:]
    y_train, y_test = y_normalized[:split_idx], y_normalized[split_idx:]
    public_ids_train, public_ids_test = public_ids[:split_idx], public_ids[split_idx:]
    
    print(f"    훈련 샘플: {len(X_train):,}, 테스트 샘플: {len(X_test):,}")
    
    # 모델 생성
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        model = create_improved_lstm_model(sequence_length, n_features, horizon)
        
        optimizer = Adam(learning_rate=0.001)
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss', 
        patience=15, 
        restore_best_weights=True,
        verbose=1
    )
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.5, 
        patience=7, 
        min_lr=0.00001,
        verbose=1
    )
    
    # 모델 학습
    print(f"\n  {'='*60}")
    print(f"  모델 학습 시작: {horizon}주 예측")
    print(f"  {'='*60}")
    print(f"  - 입력 shape: {X_train.shape}")
    print(f"  - 출력 shape: {y_train.shape}")
    print(f"  - 배치 크기: 128")
    print(f"  - 최대 epochs: 100")
    print(f"  {'='*60}\n")
    
    start_time = time.time()
    
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=100,
            batch_size=128,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
    
    elapsed_time = time.time() - start_time
    print(f"\n  학습 완료! (소요 시간: {elapsed_time:.2f}초)")
    
    # 예측
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        y_pred_scaled = model.predict(X_test, verbose=0, batch_size=128)
    
    # 역정규화 (업장별)
    y_pred = np.zeros_like(y_pred_scaled)
    y_true = np.zeros_like(y_test)
    
    for store_id in np.unique(public_ids_test):
        store_mask = public_ids_test == store_id
        if store_id in store_scalers:
            scaler = store_scalers[store_id]
            
            # 예측값 역정규화
            if len(y_pred_scaled[store_mask].shape) == 1:
                y_pred[store_mask] = scaler.inverse_transform(
                    y_pred_scaled[store_mask].reshape(-1, 1)
                ).flatten()
            else:
                y_pred[store_mask] = scaler.inverse_transform(
                    y_pred_scaled[store_mask].reshape(-1, 1)
                ).reshape(y_pred_scaled[store_mask].shape)
            
            # 실제값 역정규화
            if len(y_test[store_mask].shape) == 1:
                y_true[store_mask] = scaler.inverse_transform(
                    y_test[store_mask].reshape(-1, 1)
                ).flatten()
            else:
                y_true[store_mask] = scaler.inverse_transform(
                    y_test[store_mask].reshape(-1, 1)
                ).reshape(y_test[store_mask].shape)
    
    # 성능 평가
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100
    
    print(f"    MAE: {mae:,.2f}")
    print(f"    RMSE: {rmse:,.2f}")
    print(f"    MAPE: {mape:.2f}%")
    
    short_term_results.append({
        'horizon': horizon,
        'mae': mae,
        'rmse': rmse,
        'mape': mape
    })
    
    # 시각화 (1주 예측만)
    if horizon == 1:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 학습 곡선
        axes[0, 0].plot(history.history['loss'], label='Train Loss')
        axes[0, 0].plot(history.history['val_loss'], label='Val Loss')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 예측 vs 실제
        sample_size = min(500, len(y_true))
        axes[0, 1].scatter(y_true[:sample_size].flatten(), y_pred[:sample_size].flatten(), alpha=0.3)
        axes[0, 1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        axes[0, 1].set_xlabel('Actual')
        axes[0, 1].set_ylabel('Predicted')
        axes[0, 1].set_title('Predicted vs Actual')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 오차 분포
        errors = (y_true - y_pred).flatten()
        axes[1, 0].hist(errors, bins=50, edgecolor='black')
        axes[1, 0].set_title('Prediction Error Distribution')
        axes[1, 0].set_xlabel('Error')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].grid(True, alpha=0.3)
        
        # 상대 오차 분포
        rel_errors = (errors / (np.abs(y_true.flatten()) + 1e-8)) * 100
        axes[1, 1].hist(rel_errors, bins=50, edgecolor='black', range=(0, 200))
        axes[1, 1].set_title('Relative Error Distribution (%)')
        axes[1, 1].set_xlabel('Relative Error (%)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'results/short_term_prediction_improved_{horizon}week_v3.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Saved: short_term_prediction_improved_{horizon}week_v3.png")

# ============================================================================
# 8. 장기 예측 (6개월, 2년)
# ============================================================================
print("\n[8] 장기 예측 모델 학습 (6개월, 2년)...")

long_term_horizons = [26, 104]
long_term_results = []

for horizon in long_term_horizons:
    print(f"\n  [{horizon}주 예측 (약 {horizon//4}개월)]")
    
    sequence_length_long = 32  # 더 긴 입력 시퀀스
    
    # 시퀀스 생성
    X, y, public_ids = create_multi_feature_sequences(
        weekly_df, sequence_length_long, horizon, use_time_split=True
    )
    
    if len(X) == 0:
        print(f"    데이터 부족으로 건너뜀")
        continue
    
    print(f"    시퀀스 수: {len(X):,}")
    
    # 업장별 정규화
    X_normalized, y_normalized, store_scalers = normalize_by_store(
        X, y, public_ids, feature_idx=0
    )
    
    # 나머지 feature 정규화
    n_features = X.shape[2]
    for feat_idx in range(1, n_features):
        scaler = StandardScaler()
        feat_data = X_normalized[:, :, feat_idx].reshape(-1, 1)
        X_normalized[:, :, feat_idx] = scaler.fit_transform(feat_data).reshape(
            X_normalized[:, :, feat_idx].shape
        )
    
    # 시간 순서를 고려한 분할
    split_idx = int(len(X_normalized) * 0.8)
    X_train, X_test = X_normalized[:split_idx], X_normalized[split_idx:]
    y_train, y_test = y_normalized[:split_idx], y_normalized[split_idx:]
    public_ids_train, public_ids_test = public_ids[:split_idx], public_ids[split_idx:]
    
    # 모델 생성
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        model = create_improved_lstm_model(sequence_length_long, n_features, horizon)
        
        optimizer = Adam(learning_rate=0.0005)  # 장기 예측은 더 낮은 학습률
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    # Callbacks
    early_stop = EarlyStopping(
        monitor='val_loss', 
        patience=20, 
        restore_best_weights=True,
        verbose=1
    )
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss', 
        factor=0.5, 
        patience=10, 
        min_lr=0.00001,
        verbose=1
    )
    
    # 모델 학습
    print(f"\n  모델 학습 시작: {horizon}주 예측")
    print(f"  - 훈련 샘플: {len(X_train):,}, 테스트 샘플: {len(X_test):,}")
    
    start_time = time.time()
    
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=150,
            batch_size=64,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
    
    elapsed_time = time.time() - start_time
    print(f"  학습 완료! (소요 시간: {elapsed_time:.2f}초)")
    
    # 예측
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        y_pred_scaled = model.predict(X_test, verbose=0, batch_size=64)
    
    # 역정규화
    y_pred = np.zeros_like(y_pred_scaled)
    y_true = np.zeros_like(y_test)
    
    for store_id in np.unique(public_ids_test):
        store_mask = public_ids_test == store_id
        if store_id in store_scalers:
            scaler = store_scalers[store_id]
            
            y_pred[store_mask] = scaler.inverse_transform(
                y_pred_scaled[store_mask].reshape(-1, 1)
            ).reshape(y_pred_scaled[store_mask].shape)
            
            y_true[store_mask] = scaler.inverse_transform(
                y_test[store_mask].reshape(-1, 1)
            ).reshape(y_test[store_mask].shape)
    
    # 성능 평가
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / (np.abs(y_true) + 1e-8))) * 100
    
    print(f"    MAE: {mae:,.2f}")
    print(f"    RMSE: {rmse:,.2f}")
    print(f"    MAPE: {mape:.2f}%")
    
    long_term_results.append({
        'horizon_weeks': horizon,
        'horizon_months': horizon // 4,
        'mae': mae,
        'rmse': rmse,
        'mape': mape
    })

# ============================================================================
# 9. 결과 저장 및 요약
# ============================================================================
print("\n[9] 결과 저장 중...")

if short_term_results:
    short_term_df = pd.DataFrame(short_term_results)
    short_term_df.to_csv('results/short_term_prediction_improved_results_v3.csv', index=False, encoding='utf-8-sig')
    print("  Saved: short_term_prediction_improved_results_v3.csv")

if long_term_results:
    long_term_df = pd.DataFrame(long_term_results)
    long_term_df.to_csv('results/long_term_prediction_improved_results_v3.csv', index=False, encoding='utf-8-sig')
    print("  Saved: long_term_prediction_improved_results_v3.csv")

# 전체 결과 요약
print("\n" + "=" * 80)
print("LSTM Experiment Complete! (Improved Version)")
print("=" * 80)

if short_term_results:
    print("\n단기 예측 결과:")
    print(pd.DataFrame(short_term_results))

if long_term_results:
    print("\n장기 예측 결과:")
    print(pd.DataFrame(long_term_results))

print("\n개선 사항:")
print("1. 다중 feature 사용 (sales_card, sales_ratio, 이동평균, 트렌드 등)")
print("2. 시간 순서를 고려한 데이터 분할")
print("3. 업장별 정규화")
print("4. Bidirectional LSTM + Attention 메커니즘")
print("5. 시계열 특성 추가 (이동평균, 트렌드, 변동성)")

if short_term_results and long_term_results:
    short_mape = short_term_results[0]['mape']
    long_mape_6m = long_term_results[0]['mape'] if len(long_term_results) > 0 else None
    
    print(f"\n결론:")
    print(f"- 단기 예측 (1주): MAPE {short_mape:.2f}%")
    if long_mape_6m:
        print(f"- 장기 예측 (6개월): MAPE {long_mape_6m:.2f}%")
        
        # 이전 결과와 비교
        prev_short_mape = 144.87
        prev_long_mape = 156.49
        
        improvement_short = ((prev_short_mape - short_mape) / prev_short_mape) * 100
        improvement_long = ((prev_long_mape - long_mape_6m) / prev_long_mape) * 100
        
        print(f"\n성능 개선:")
        print(f"- 단기 예측: {improvement_short:.1f}% 개선 (이전: {prev_short_mape:.2f}% → 현재: {short_mape:.2f}%)")
        print(f"- 장기 예측: {improvement_long:.1f}% 개선 (이전: {prev_long_mape:.2f}% → 현재: {long_mape_6m:.2f}%)")

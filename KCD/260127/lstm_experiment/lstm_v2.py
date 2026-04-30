"""
LSTM Experiment for Sales Prediction (Optimized)
- 단기 예측 (1-4주)
- 장기 예측 (6개월, 2년)
- 성능 평가 및 비교

최적화 사항:
- GPU 1번 사용 (GPU 0번은 바쁨)
- 배치 크기 증가 (32→256, 16→128)
- LSTM 입력 shape 수정 (features 차원 추가)
"""

import os
import sys
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

# TensorFlow 경고 메시지 억제 (import 전에 설정)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# GPU 선택 (기본값: GPU 1번 사용, GPU 0번은 바쁨)
USE_GPU_ID = 3  # 0, 1, 2, 3 중 선택 가능

# TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    print("TensorFlow version:", tf.__version__)
    
    # TensorFlow 로거 레벨 추가 설정 (경고 메시지 억제)
    tf.get_logger().setLevel('ERROR')
except ImportError:
    print("ERROR: TensorFlow가 설치되지 않았습니다.")
    print("다음 명령어로 설치해주세요: pip install tensorflow")
    sys.exit(1)

# GPU 설정 확인 및 구성
print("\nGPU 설정 확인:")
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"  GPU 사용 가능: {len(gpus)}개")
    for i, gpu in enumerate(gpus):
        print(f"    - GPU {i}: {gpu}")
    
    # 특정 GPU만 사용하도록 설정
    if USE_GPU_ID < len(gpus):
        # 다른 GPU는 사용하지 않도록 설정
        for i, gpu in enumerate(gpus):
            if i != USE_GPU_ID:
                tf.config.set_visible_devices([], 'GPU')
                break
        tf.config.set_visible_devices([gpus[USE_GPU_ID]], 'GPU')
        print(f"  ✅ GPU {USE_GPU_ID}번만 사용하도록 설정")
    else:
        print(f"  ⚠️  GPU {USE_GPU_ID}번이 없습니다. GPU 0번 사용")
        USE_GPU_ID = 0
    
    # GPU 메모리 증가 허용
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("  GPU 메모리 증가 모드 활성화")
    except RuntimeError as e:
        print(f"  GPU 메모리 설정 오류: {e}")
    
    # 혼합 정밀도 사용 (속도 향상)
    try:
        tf.keras.mixed_precision.set_global_policy('mixed_float16')
        print("  혼합 정밀도 (mixed_float16) 활성화")
    except:
        print("  혼합 정밀도 사용 불가 (선택사항)")
else:
    print("  GPU 사용 불가 - CPU 사용")
    print("  (GPU 사용 시 10-100배 빠른 학습 가능)")

# 한글 폰트 설정
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
os.makedirs('results', exist_ok=True)

print("=" * 80)
print("LSTM Experiment for Sales Prediction (Optimized)")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

# 시계열 데이터 로드
weekly_df = pd.read_parquet('../original_data/weekly_processed.parquet')
cluster_labels = pd.read_csv('../result_csv/cluster_labels.csv')

print(f"weekly_processed.parquet: {weekly_df.shape}")
print(f"cluster_labels: {cluster_labels.shape}")

# 클러스터 레이블 병합
weekly_df = weekly_df.merge(cluster_labels, on='public_id', how='inner')
print(f"병합 후 데이터: {weekly_df.shape}")

# day_after1=0 제외
weekly_df = weekly_df[weekly_df['day_after1'] != 0]

# ============================================================================
# 2. 시계열 데이터 준비
# ============================================================================
print("\n[2] 시계열 데이터 준비 중...")

# 각 업장별 시계열 생성
def create_sequences(data, sequence_length, prediction_horizon):
    """
    시계열 데이터를 시퀀스로 변환
    sequence_length: 입력 시퀀스 길이
    prediction_horizon: 예측할 미래 시점 수
    """
    X, y = [], []
    public_ids = data['public_id'].unique()
    
    for pid in public_ids:
        store_data = data[data['public_id'] == pid].sort_values('day_after1')
        sales_values = store_data['sales_card'].values
        
        if len(sales_values) < sequence_length + prediction_horizon:
            continue
        
        for i in range(len(sales_values) - sequence_length - prediction_horizon + 1):
            X.append(sales_values[i:i+sequence_length])
            y.append(sales_values[i+sequence_length:i+sequence_length+prediction_horizon])
    
    return np.array(X), np.array(y)

# 시계열 길이 필터링 (최소 50주 이상)
min_weeks = 50
store_counts = weekly_df.groupby('public_id').size()
valid_stores = store_counts[store_counts >= min_weeks].index
weekly_df = weekly_df[weekly_df['public_id'].isin(valid_stores)]

print(f"최소 {min_weeks}주 이상 데이터를 가진 업장 수: {len(valid_stores)}")

# ============================================================================
# 3. 단기 예측 (1-4주)
# ============================================================================
print("\n[3] 단기 예측 모델 학습 (1-4주)...")

sequence_length = 12  # 12주 입력
prediction_horizons = [1, 2, 4]  # 1주, 2주, 4주 예측

short_term_results = []

for horizon in prediction_horizons:
    print(f"\n  [{horizon}주 예측]")
    
    # 시퀀스 생성
    X, y = create_sequences(weekly_df, sequence_length, horizon)
    
    if len(X) == 0:
        print(f"    데이터 부족으로 건너뜀")
        continue
    
    print(f"    시퀀스 수: {len(X):,}")
    print(f"    입력 shape: {X.shape}, 출력 shape: {y.shape}")
    
    # 데이터 정규화
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_reshaped = X.reshape(-1, X.shape[-1])
    X_scaled = scaler_X.fit_transform(X_reshaped)
    X_scaled = X_scaled.reshape(X.shape)
    
    y_reshaped = y.reshape(-1, y.shape[-1])
    y_scaled = scaler_y.fit_transform(y_reshaped)
    y_scaled = y_scaled.reshape(y.shape)
    
    # 훈련/테스트 분할 (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
    y_train, y_test = y_scaled[:split_idx], y_scaled[split_idx:]
    
    # LSTM 입력 형태로 변환: (samples, timesteps, features)
    # 현재: (samples, timesteps) -> 변환: (samples, timesteps, 1)
    if len(X_train.shape) == 2:
        X_train = np.expand_dims(X_train, axis=-1)
        X_test = np.expand_dims(X_test, axis=-1)
    
    print(f"    LSTM 입력 shape: {X_train.shape}")
    
    # 배치 크기 최적화 (GPU 활용도 향상)
    batch_size = 256  # 32 -> 256으로 증가 (약 8배 빠름)
    
    # LSTM 모델 구성
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        model = Sequential([
            LSTM(64, return_sequences=True, input_shape=(sequence_length, 1)),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(horizon, dtype='float32')  # 출력 레이어를 float32로 명시적 설정 (혼합 정밀도 문제 해결)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    # Early stopping
    early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=0.0001)
    
    # 모델 학습
    print(f"\n  {'='*60}")
    print(f"  모델 학습 시작: {horizon}주 예측")
    print(f"  {'='*60}")
    
    # GPU 사용 확인
    if gpus and USE_GPU_ID < len(gpus):
        try:
            with tf.device(f'/GPU:{USE_GPU_ID}'):
                test_tensor = tf.constant([[1.0]])
                _ = tf.matmul(test_tensor, test_tensor)
            print(f"  ✅ GPU 사용 중: GPU {USE_GPU_ID}번")
        except:
            print(f"  ⚠️  GPU {USE_GPU_ID}번 사용 불가 - CPU 사용 중")
    else:
        print(f"  ℹ️  CPU 사용 중")
    
    print(f"  - 입력 shape: {X_train.shape}")
    print(f"  - 출력 shape: {y_train.shape}")
    print(f"  - 훈련 샘플 수: {len(X_train):,}")
    print(f"  - 배치 크기: {batch_size} (최적화됨)")
    print(f"  - 예상 steps per epoch: {len(X_train) // batch_size:,}")
    print(f"  - 최대 epochs: 50")
    print(f"  {'='*60}\n")
    
    start_time = time.time()
    
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=50,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
    
    elapsed_time = time.time() - start_time
    print(f"\n  {'='*60}")
    print(f"  학습 완료!")
    print(f"  - 소요 시간: {elapsed_time:.2f}초 ({elapsed_time/60:.2f}분)")
    print(f"  - 실제 학습 epochs: {len(history.history['loss'])}")
    print(f"  - 최종 train loss: {history.history['loss'][-1]:.6f}")
    print(f"  - 최종 val loss: {history.history['val_loss'][-1]:.6f}")
    print(f"  {'='*60}\n")
    
    # 예측
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        y_pred_scaled = model.predict(X_test, verbose=0)
    
    # 예측값 확인 (디버깅)
    print(f"    예측값 (정규화된) 범위: min={np.min(y_pred_scaled):.6f}, max={np.max(y_pred_scaled):.6f}")
    
    # 무한대나 NaN 확인 및 처리
    if np.any(np.isinf(y_pred_scaled)) or np.any(np.isnan(y_pred_scaled)):
        print(f"    ⚠️  예측값에 무한대 또는 NaN이 있습니다.")
        inf_count = np.sum(np.isinf(y_pred_scaled))
        nan_count = np.sum(np.isnan(y_pred_scaled))
        print(f"       무한대: {inf_count}개, NaN: {nan_count}개")
        y_pred_scaled = np.nan_to_num(y_pred_scaled, nan=0.0, posinf=1.0, neginf=0.0)
        y_pred_scaled = np.clip(y_pred_scaled, 0.0, 1.0)  # MinMaxScaler 범위로 클리핑
    
    # 역정규화
    y_pred_reshaped = y_pred_scaled.reshape(-1, horizon)
    y_test_reshaped = y_test.reshape(-1, horizon)
    
    # 역정규화 전 원본 데이터 범위 확인
    print(f"    원본 y 범위: min={np.min(y):.2f}, max={np.max(y):.2f}")
    print(f"    Scaler min: {scaler_y.data_min_}, max: {scaler_y.data_max_}")
    
    y_pred = scaler_y.inverse_transform(y_pred_reshaped)
    y_true = scaler_y.inverse_transform(y_test_reshaped)
    
    # 역정규화 후 확인
    print(f"    역정규화 후 예측값 범위: min={np.min(y_pred):.2f}, max={np.max(y_pred):.2f}")
    print(f"    역정규화 후 실제값 범위: min={np.min(y_true):.2f}, max={np.max(y_true):.2f}")
    
    # 무한대나 NaN 확인 및 처리
    if np.any(np.isinf(y_pred)) or np.any(np.isnan(y_pred)):
        print(f"    ⚠️  역정규화 후 무한대 또는 NaN이 있습니다. 클리핑합니다.")
        y_min, y_max = np.nanmin(y_true), np.nanmax(y_true)
        y_pred = np.clip(y_pred, y_min * 0.1, y_max * 10)
        y_pred = np.nan_to_num(y_pred, nan=y_min, posinf=y_max*10, neginf=y_min*0.1)
    
    # 성능 평가
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
    
    print(f"    MAE: {mae:.2f}")
    print(f"    RMSE: {rmse:.2f}")
    print(f"    MAPE: {mape:.2f}%")
    
    short_term_results.append({
        'horizon': horizon,
        'mae': mae,
        'rmse': rmse,
        'mape': mape
    })
    
    # 예측 결과 시각화 (샘플)
    if horizon == 1:  # 1주 예측만 시각화
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # 학습 곡선
        axes[0, 0].plot(history.history['loss'], label='Train Loss')
        axes[0, 0].plot(history.history['val_loss'], label='Val Loss')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 예측 vs 실제 (첫 100개 샘플)
        sample_size = min(100, len(y_true))
        axes[0, 1].scatter(y_true[:sample_size], y_pred[:sample_size], alpha=0.5)
        axes[0, 1].plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', lw=2)
        axes[0, 1].set_xlabel('Actual')
        axes[0, 1].set_ylabel('Predicted')
        axes[0, 1].set_title('Predicted vs Actual')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 시계열 예측 예시 (5개 샘플)
        for i in range(min(5, len(y_test))):
            axes[1, 0].plot(range(sequence_length), X_test[i].flatten(), label=f'Input {i+1}', alpha=0.7)
        axes[1, 0].set_title('Input Sequences (Sample)')
        axes[1, 0].set_xlabel('Week')
        axes[1, 0].set_ylabel('Sales (Normalized)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 예측 오차 분포
        errors = y_true.flatten() - y_pred.flatten()
        axes[1, 1].hist(errors, bins=50, edgecolor='black')
        axes[1, 1].set_title('Prediction Error Distribution')
        axes[1, 1].set_xlabel('Error')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'results/short_term_prediction_{horizon}week.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"    Saved: short_term_prediction_{horizon}week.png")

# ============================================================================
# 4. 장기 예측 (6개월, 2년)
# ============================================================================
print("\n[4] 장기 예측 모델 학습 (6개월, 2년)...")

# 6개월 = 약 26주, 2년 = 약 104주
long_term_horizons = [26, 104]

long_term_results = []

for horizon in long_term_horizons:
    print(f"\n  [{horizon}주 예측 (약 {horizon//4}개월)]")
    
    # 더 긴 입력 시퀀스 사용
    sequence_length_long = 24
    
    # 시퀀스 생성
    X, y = create_sequences(weekly_df, sequence_length_long, horizon)
    
    if len(X) == 0:
        print(f"    데이터 부족으로 건너뜀")
        continue
    
    print(f"    시퀀스 수: {len(X):,}")
    
    # 데이터 정규화
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()
    
    X_reshaped = X.reshape(-1, X.shape[-1])
    X_scaled = scaler_X.fit_transform(X_reshaped)
    X_scaled = X_scaled.reshape(X.shape)
    
    y_reshaped = y.reshape(-1, y.shape[-1])
    y_scaled = scaler_y.fit_transform(y_reshaped)
    y_scaled = y_scaled.reshape(y.shape)
    
    # 훈련/테스트 분할
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X_scaled[:split_idx], X_scaled[split_idx:]
    y_train, y_test = y_scaled[:split_idx], y_scaled[split_idx:]
    
    # LSTM 입력 형태로 변환
    if len(X_train.shape) == 2:
        X_train = np.expand_dims(X_train, axis=-1)
        X_test = np.expand_dims(X_test, axis=-1)
    
    print(f"    LSTM 입력 shape: {X_train.shape}")
    
    # 배치 크기 최적화
    batch_size = 128  # 16 -> 128로 증가 (약 8배 빠름)
    
    # 장기 예측을 위한 더 깊은 모델
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(sequence_length_long, 1)),
            Dropout(0.3),
            LSTM(64, return_sequences=True),
            Dropout(0.3),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(horizon, dtype='float32')  # 출력 레이어를 float32로 명시적 설정 (혼합 정밀도 문제 해결)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    
    # Early stopping
    early_stop = EarlyStopping(monitor='val_loss', patience=15, restore_best_weights=True)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=7, min_lr=0.0001)
    
    # 모델 학습
    print(f"\n  {'='*60}")
    print(f"  모델 학습 시작: {horizon}주 예측 (약 {horizon//4}개월)")
    print(f"  {'='*60}")
    
    # GPU 사용 확인
    if gpus and USE_GPU_ID < len(gpus):
        try:
            with tf.device(f'/GPU:{USE_GPU_ID}'):
                test_tensor = tf.constant([[1.0]])
                _ = tf.matmul(test_tensor, test_tensor)
            print(f"  ✅ GPU 사용 중: GPU {USE_GPU_ID}번")
        except:
            print(f"  ⚠️  GPU {USE_GPU_ID}번 사용 불가 - CPU 사용 중")
    else:
        print(f"  ℹ️  CPU 사용 중")
    
    print(f"  - 입력 shape: {X_train.shape}")
    print(f"  - 출력 shape: {y_train.shape}")
    print(f"  - 훈련 샘플 수: {len(X_train):,}")
    print(f"  - 배치 크기: {batch_size} (최적화됨)")
    print(f"  - 예상 steps per epoch: {len(X_train) // batch_size:,}")
    print(f"  - 최대 epochs: 100")
    print(f"  {'='*60}\n")
    
    start_time = time.time()
    
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        history = model.fit(
            X_train, y_train,
            validation_split=0.2,
            epochs=100,
            batch_size=batch_size,
            callbacks=[early_stop, reduce_lr],
            verbose=1
        )
    
    elapsed_time = time.time() - start_time
    print(f"\n  {'='*60}")
    print(f"  학습 완료!")
    print(f"  - 소요 시간: {elapsed_time:.2f}초 ({elapsed_time/60:.2f}분)")
    print(f"  - 실제 학습 epochs: {len(history.history['loss'])}")
    print(f"  - 최종 train loss: {history.history['loss'][-1]:.6f}")
    print(f"  - 최종 val loss: {history.history['val_loss'][-1]:.6f}")
    print(f"  {'='*60}\n")
    
    # 예측
    with tf.device(f'/GPU:{USE_GPU_ID}'):
        y_pred_scaled = model.predict(X_test, verbose=0)
    
    # 예측값 확인 (디버깅)
    print(f"    예측값 (정규화된) 범위: min={np.min(y_pred_scaled):.6f}, max={np.max(y_pred_scaled):.6f}")
    
    # 무한대나 NaN 확인 및 처리
    if np.any(np.isinf(y_pred_scaled)) or np.any(np.isnan(y_pred_scaled)):
        print(f"    ⚠️  예측값에 무한대 또는 NaN이 있습니다.")
        inf_count = np.sum(np.isinf(y_pred_scaled))
        nan_count = np.sum(np.isnan(y_pred_scaled))
        print(f"       무한대: {inf_count}개, NaN: {nan_count}개")
        y_pred_scaled = np.nan_to_num(y_pred_scaled, nan=0.0, posinf=1.0, neginf=0.0)
        y_pred_scaled = np.clip(y_pred_scaled, 0.0, 1.0)  # MinMaxScaler 범위로 클리핑
    
    # 역정규화
    y_pred_reshaped = y_pred_scaled.reshape(-1, horizon)
    y_test_reshaped = y_test.reshape(-1, horizon)
    
    # 역정규화 전 원본 데이터 범위 확인
    print(f"    원본 y 범위: min={np.min(y):.2f}, max={np.max(y):.2f}")
    print(f"    Scaler min: {scaler_y.data_min_}, max: {scaler_y.data_max_}")
    
    y_pred = scaler_y.inverse_transform(y_pred_reshaped)
    y_true = scaler_y.inverse_transform(y_test_reshaped)
    
    # 역정규화 후 확인
    print(f"    역정규화 후 예측값 범위: min={np.min(y_pred):.2f}, max={np.max(y_pred):.2f}")
    print(f"    역정규화 후 실제값 범위: min={np.min(y_true):.2f}, max={np.max(y_true):.2f}")
    
    # 무한대나 NaN 확인 및 처리
    if np.any(np.isinf(y_pred)) or np.any(np.isnan(y_pred)):
        print(f"    ⚠️  역정규화 후 무한대 또는 NaN이 있습니다. 클리핑합니다.")
        y_min, y_max = np.nanmin(y_true), np.nanmax(y_true)
        y_pred = np.clip(y_pred, y_min * 0.1, y_max * 10)
        y_pred = np.nan_to_num(y_pred, nan=y_min, posinf=y_max*10, neginf=y_min*0.1)
    
    # 성능 평가
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mape = np.mean(np.abs((y_true - y_pred) / (y_true + 1e-8))) * 100
    
    print(f"    MAE: {mae:.2f}")
    print(f"    RMSE: {rmse:.2f}")
    print(f"    MAPE: {mape:.2f}%")
    
    long_term_results.append({
        'horizon_weeks': horizon,
        'horizon_months': horizon // 4,
        'mae': mae,
        'rmse': rmse,
        'mape': mape
    })
    
    # 예측 결과 시각화
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 학습 곡선
    axes[0, 0].plot(history.history['loss'], label='Train Loss')
    axes[0, 0].plot(history.history['val_loss'], label='Val Loss')
    axes[0, 0].set_title('Model Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 예측 vs 실제 (평균)
    y_true_mean = np.mean(y_true, axis=0)
    y_pred_mean = np.mean(y_pred, axis=0)
    weeks = range(horizon)
    
    axes[0, 1].plot(weeks, y_true_mean, label='Actual Mean', marker='o')
    axes[0, 1].plot(weeks, y_pred_mean, label='Predicted Mean', marker='s')
    axes[0, 1].set_title(f'Mean Prediction ({horizon} weeks)')
    axes[0, 1].set_xlabel('Weeks Ahead')
    axes[0, 1].set_ylabel('Sales')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 샘플 예측 (3개)
    for i in range(min(3, len(y_test))):
        axes[1, 0].plot(weeks, y_true[i], label=f'Actual {i+1}', alpha=0.7, marker='o')
        axes[1, 0].plot(weeks, y_pred[i], label=f'Predicted {i+1}', alpha=0.7, marker='s', linestyle='--')
    axes[1, 0].set_title('Sample Predictions')
    axes[1, 0].set_xlabel('Weeks Ahead')
    axes[1, 0].set_ylabel('Sales')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 오차 분포
    errors = (y_true - y_pred).flatten()
    axes[1, 1].hist(errors, bins=50, edgecolor='black')
    axes[1, 1].set_title('Prediction Error Distribution')
    axes[1, 1].set_xlabel('Error')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'results/long_term_prediction_{horizon}weeks.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    Saved: long_term_prediction_{horizon}weeks.png")

# ============================================================================
# 5. 결과 저장 및 요약
# ============================================================================
print("\n[5] 결과 저장 중...")

# 단기 예측 결과
if short_term_results:
    short_term_df = pd.DataFrame(short_term_results)
    short_term_df.to_csv('results/short_term_prediction_results.csv', index=False, encoding='utf-8-sig')
    print("  Saved: short_term_prediction_results.csv")

# 장기 예측 결과
if long_term_results:
    long_term_df = pd.DataFrame(long_term_results)
    long_term_df.to_csv('results/long_term_prediction_results.csv', index=False, encoding='utf-8-sig')
    print("  Saved: long_term_prediction_results.csv")

# 전체 결과 요약
print("\n" + "=" * 80)
print("LSTM Experiment Complete!")
print("=" * 80)

if short_term_results:
    print("\n단기 예측 결과:")
    print(pd.DataFrame(short_term_results))

if long_term_results:
    print("\n장기 예측 결과:")
    print(pd.DataFrame(long_term_results))

print("\n결론:")
if short_term_results and long_term_results:
    short_mape = short_term_results[0]['mape']  # 1주 예측
    long_mape_6m = long_term_results[0]['mape'] if len(long_term_results) > 0 else None
    
    print(f"- 단기 예측 (1주): MAPE {short_mape:.2f}%")
    if long_mape_6m:
        print(f"- 장기 예측 (6개월): MAPE {long_mape_6m:.2f}%")
        if long_mape_6m > short_mape * 2:
            print("  → 장기 예측의 정확도가 크게 떨어짐 (예상된 결과)")
        else:
            print("  → 장기 예측도 상대적으로 양호한 성능")
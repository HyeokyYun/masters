import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, f1_score, classification_report
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import os

# 시각화 설정
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("Hybrid Model Training: Basic Statistics + LSTM Embeddings + XGBoost")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

# 1) 원본 시계열 데이터 (기초 통계량 생성용)
weekly_df = pd.read_parquet('../original_data/weekly_processed.parquet')
# 2) 타겟 레이블 (Cluster 0~8)
cluster_labels = pd.read_csv('../result_csv/cluster_labels.csv')
# 3) 방금 생성한 LSTM 특징 (Embedding)
lstm_features = pd.read_csv('../result_csv/lstm_extracted_features.csv')

print(f" - Weekly Data: {weekly_df.shape}")
print(f" - Cluster Labels: {cluster_labels.shape}")
print(f" - LSTM Features: {lstm_features.shape}")

# ============================================================================
# 2. 베이스라인 피처 엔지니어링 (기존 연구 내용 반영)
# ============================================================================
print("\n[2] 기초 통계 피처 생성 (Baseline)...")

# 매장별로 정렬
weekly_df = weekly_df.sort_values(['public_id', 'day_after1'])

# 기초 통계량 집계 함수
def calculate_store_stats(x):
    stats = {}
    sales = x['sales_card'].values
    
    # 전체 기간 통계
    stats['total_mean'] = np.mean(sales)
    stats['total_std'] = np.std(sales)
    stats['total_max'] = np.max(sales)
    
    # 초기/최근 통계
    if len(sales) >= 12:
        stats['initial_4w_mean'] = np.mean(sales[:4])
        stats['recent_4w_mean'] = np.mean(sales[-4:])
        
        # 성장률 (0 나누기 방지)
        eps = 1e-6
        stats['growth_rate'] = (stats['recent_4w_mean'] - stats['initial_4w_mean']) / (stats['initial_4w_mean'] + eps)
        
        # 최근 변동성
        stats['recent_volatility'] = np.std(sales[-12:])
    else:
        stats['initial_4w_mean'] = np.mean(sales)
        stats['recent_4w_mean'] = np.mean(sales)
        stats['growth_rate'] = 0
        stats['recent_volatility'] = np.std(sales)
        
    return pd.Series(stats)

# [수정 1] FutureWarning 해결 (include_groups=False 추가)
basic_features = weekly_df.groupby('public_id').apply(calculate_store_stats, include_groups=False).reset_index()
print(f" - 기초 통계 피처 생성 완료: {basic_features.shape}")

# ============================================================================
# 2.5. 업종(Category) 정보 추출 (별도 파일 로드 필요)
# ============================================================================
print("\n[2.5] 업종 정보 추출 및 인코딩...")

# [수정 2] 업종 정보가 있는 파일을 따로 로드해야 합니다.
# (파일 경로와 이름을 실제 업종 정보가 있는 파일로 변경해주세요!)
try:
    # 예: store_info.csv 혹은 raw_data.parquet 등
    store_meta_df = pd.read_csv('../original_data/meta_processed.csv') 
    # 만약 parquet라면: pd.read_parquet('../original_data/original_data.parquet')
    
    print(" - 업종 정보 파일 로드 성공")
except FileNotFoundError:
    print("⚠️ 오류: 업종 정보 파일을 찾을 수 없습니다. 경로를 확인해주세요.")
    # 임시로 더미 데이터 생성 (에러 방지용, 실제 분석시엔 꼭 파일 연결 필요)
    store_meta_df = pd.DataFrame({
        'public_id': weekly_df['public_id'].unique(),
        'depth_1': 'Unknown',
        'depth_2': 'Unknown'
    })

# 필요한 컬럼만 선택 및 중복 제거
store_info = store_meta_df[['public_id', 'depth_1', 'depth_2']].drop_duplicates()

# 라벨 인코딩
from sklearn.preprocessing import LabelEncoder
le_d1 = LabelEncoder()
le_d2 = LabelEncoder()

# 문자열로 변환 후 인코딩 (결측치 처리 포함)
store_info['depth_1'] = le_d1.fit_transform(store_info['depth_1'].fillna('Unknown').astype(str))
store_info['depth_2'] = le_d2.fit_transform(store_info['depth_2'].fillna('Unknown').astype(str))

print(f" - 업종 정보 준비 완료: {store_info.shape}")

# ============================================================================
# 3. 데이터 병합 (Hybrid Dataset 구성)
# ============================================================================
print("\n[3] 최종 데이터 병합...")

# 1) 기초 통계 + LSTM 특징 병합
merged_df = pd.merge(basic_features, lstm_features, on='public_id', how='inner')

# 2) [추가] 업종 정보 병합
merged_df = pd.merge(merged_df, store_info, on='public_id', how='inner')

# 3) 타겟 레이블 병합
final_df = pd.merge(merged_df, cluster_labels[['public_id', 'cluster']], on='public_id', how='inner')

# 4) 불필요한 컬럼 제거
X = final_df.drop(columns=['public_id', 'cluster'])
y = final_df['cluster']

print(f" - 최종 학습 데이터셋 형태: X={X.shape}, y={y.shape}")
print(f" - 포함된 변수: {X.columns.tolist()}")

# ============================================================================
# 4. XGBoost 모델 학습
# ============================================================================
print("\n[4] XGBoost 학습 시작 (GPU 모드)...")

# Train/Test 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# XGBoost 모델 정의 (다중 분류)
# 사용자의 이전 실험 최고 성능 조건(이상치 미제거, 지역변수 제거)을 따름
xgb_model = xgb.XGBClassifier(
    n_estimators=1000,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='multi:softprob',
    num_class=9,
    tree_method='hist',  # GPU 가속
    device='cuda',       # GPU 사용 (안되면 'cpu'로 변경)
    random_state=42,
    early_stopping_rounds=50
)

# 학습
xgb_model.fit(
    X_train, y_train,
    eval_set=[(X_train, y_train), (X_test, y_test)],
    verbose=100
)

# ============================================================================
# 5. 성능 평가
# ============================================================================
print("\n[5] 최종 성능 평가...")

y_pred = xgb_model.predict(X_test)

acc = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\n✅ Accuracy: {acc:.4f}")
print(f"✅ F1-Score (Weighted): {f1:.4f}")

# 기존 최고 기록과 비교
prev_best_f1 = 0.726
print(f"\n[비교] 기존 Best F1 ({prev_best_f1}) 대비: {f1 - prev_best_f1:+.4f}")

if f1 > prev_best_f1:
    print("🎉 성능 향상 성공! LSTM 특징이 효과적입니다.")
else:
    print("🤔 성능이 비슷하거나 낮습니다. 피처 중요도를 확인해보세요.")

print("\n[Classification Report]")
print(classification_report(y_test, y_pred))

# ============================================================================
# 6. 변수 중요도 시각화 (LSTM 변수 기여도 확인)
# ============================================================================
print("\n[6] 변수 중요도 분석...")

feature_importance = pd.DataFrame({
    'Feature': X.columns,
    'Importance': xgb_model.feature_importances_
}).sort_values('Importance', ascending=False)

# 상위 20개만 시각화
plt.figure(figsize=(12, 8))
sns.barplot(x='Importance', y='Feature', data=feature_importance.head(20))
plt.title('Top 20 Features Importance (Basic + LSTM)')
plt.tight_layout()
plt.savefig('../result_csv/hybrid_feature_importance.png')
plt.show()

# LSTM 변수가 상위 20개에 몇 개나 포함되었는지 확인
lstm_cols_in_top20 = [c for c in feature_importance.head(20)['Feature'] if 'lstm_' in c]
print(f"\n💡 상위 20개 중요 변수 중 LSTM 특징 개수: {len(lstm_cols_in_top20)}개")
print(f"   목록: {lstm_cols_in_top20}")

# 전체 중요도 저장
feature_importance.to_csv('../result_csv/hybrid_feature_importance.csv', index=False)
print("변수 중요도 저장 완료: ../result_csv/hybrid_feature_importance.csv")
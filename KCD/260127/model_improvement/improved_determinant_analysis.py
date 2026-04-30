"""
Improved Determinant Analysis with Enhanced Noise Removal
- 강화된 노이즈 제거 (IQR, Z-score)
- KNN Imputation
- 특성 선택
- 하이퍼파라미터 튜닝
- 교차 검증
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression
from scipy import stats
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Noto Sans CJK KR'
plt.rcParams['axes.unicode_minus'] = False

# 결과 저장 디렉토리
os.makedirs('results', exist_ok=True)

print("=" * 80)
print("Improved Determinant Analysis (WITHOUT Outlier Removal)")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

# 상위 디렉토리에서 데이터 로드
df = pd.read_csv('../basic_data/store_features_for_analysis.csv')
print(f"데이터 shape: {df.shape}")
print(f"Cluster distribution:")
print(df['cluster'].value_counts().sort_index())

# ============================================================================
# 2. 강화된 데이터 전처리
# ============================================================================
print("\n[2] 강화된 데이터 전처리 중...")

# 클러스터를 정수형으로 변환
df['cluster'] = df['cluster'].astype(int)

# 범주형 변수 인코딩
print("  - Encoding categorical variables...")
categorical_cols = ['sigungu', 'dong', 'depth_1', 'depth_2', 'depth_3', 'age']

df_encoded = df.copy()
for col in categorical_cols:
    if col in df_encoded.columns:
        dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
        df_encoded = pd.concat([df_encoded, dummies], axis=1)
        df_encoded = df_encoded.drop(columns=[col])

# 숫자형 변수 선택
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [col for col in numeric_cols if col not in ['cluster', 'public_id', 'total_weeks']]

# 2-1. 결측치 처리 (KNN Imputation)
print("  - Handling missing values with KNN Imputation...")
missing_info = {}
for col in numeric_cols:
    missing_count = df[col].isna().sum()
    if missing_count > 0:
        missing_info[col] = missing_count
        print(f"    {col}: {missing_count} missing values")

if missing_info:
    # KNN Imputer 사용
    imputer = KNNImputer(n_neighbors=5)
    df_encoded[numeric_cols] = imputer.fit_transform(df_encoded[numeric_cols])
    print(f"  - KNN Imputation 완료")
else:
    print("  - 결측치 없음")

# 2-2. 이상치 처리 없음 (원본 데이터 유지)
print("  - Outlier removal: SKIPPED (원본 데이터 유지)")

# 2-3. 특성 선택
print("  - Feature selection...")

# 낮은 분산 특성 제거
variance_selector = VarianceThreshold(threshold=0.01)
X_temp = df_encoded[numeric_cols].copy()
variance_selector.fit(X_temp)
selected_features = X_temp.columns[variance_selector.get_support()].tolist()
print(f"    Variance threshold: {len(selected_features)}/{len(numeric_cols)} features selected")

# 파생 변수 생성
print("  - Creating derived variables...")
if 'avg_sales_card' in df_encoded.columns and 'business_square_size' in df_encoded.columns:
    df_encoded['sales_per_area'] = df_encoded['avg_sales_card'] / (df_encoded['business_square_size'] + 1)

if 'avg_sales_card' in df_encoded.columns and 'avg_customer' in df_encoded.columns:
    df_encoded['sales_per_customer'] = df_encoded['avg_sales_card'] / (df_encoded['avg_customer'] + 1)

# X, y 준비
X_cols = [col for col in df_encoded.columns if col not in ['cluster', 'public_id', 'open_month', 'total_weeks']]
X = df_encoded[X_cols].copy()
y = df_encoded['cluster'].copy()

print(f"  Final number of variables: {len(X_cols)}")
print(f"  Number of samples: {len(X)}")

# ============================================================================
# 3. 훈련/테스트 분할
# ============================================================================
print("\n[3] 훈련/테스트 분할 중...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

print(f"  Training set: {len(X_train)} samples")
print(f"  Test set: {len(X_test)} samples")

# 스케일링
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 4. 하이퍼파라미터 튜닝 및 모델 학습
# ============================================================================
print("\n[4] 모델 학습 및 하이퍼파라미터 튜닝 중...")

# 4-1. Logistic Regression (GridSearch)
print("\n[4-1] Logistic Regression with GridSearch...")
lr_param_grid = {
    'C': [0.1, 1, 10, 100],
    'max_iter': [1000, 2000, 3000, 5000]
}

# scikit-learn 버전 호환성을 위해 multi_class 제거 (lbfgs solver가 자동으로 multinomial 처리)
# try:
#     lr_base = LogisticRegression(
#         multi_class='multinomial',
#         solver='lbfgs',
#         class_weight='balanced',
#         random_state=42
#     )
# except TypeError:
#     # 구버전 scikit-learn 호환
#     lr_base = LogisticRegression(
#         solver='lbfgs',
#         class_weight='balanced',
#         random_state=42
#     )
lr_base = LogisticRegression(
    solver='lbfgs',
    class_weight='balanced',
    max_iter=2000,
    random_state=42
)

lr_grid = GridSearchCV(lr_base, lr_param_grid, cv=5, scoring='f1_weighted', n_jobs=-1)
lr_grid.fit(X_train_scaled, y_train)

lr_model = lr_grid.best_estimator_
y_pred_lr = lr_model.predict(X_test_scaled)
lr_accuracy = accuracy_score(y_test, y_pred_lr)
lr_f1 = f1_score(y_test, y_pred_lr, average='weighted')

print(f"  Best params: {lr_grid.best_params_}")
print(f"  Accuracy: {lr_accuracy:.4f}")
print(f"  F1-score (weighted): {lr_f1:.4f}")

# 4-2. Random Forest (GridSearch)
print("\n[4-2] Random Forest with GridSearch...")
rf_param_grid = {
    'n_estimators': [200, 300, 400],
    'max_depth': [10, 15, 20],
    'min_samples_split': [5, 10, 15]
}

rf_base = RandomForestClassifier(
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

rf_grid = GridSearchCV(rf_base, rf_param_grid, cv=5, scoring='f1_weighted', n_jobs=-1, verbose=1)
rf_grid.fit(X_train, y_train)

rf_model = rf_grid.best_estimator_
y_pred_rf = rf_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, y_pred_rf)
rf_f1 = f1_score(y_test, y_pred_rf, average='weighted')

print(f"  Best params: {rf_grid.best_params_}")
print(f"  Accuracy: {rf_accuracy:.4f}")
print(f"  F1-score (weighted): {rf_f1:.4f}")

# 변수 중요도
rf_importance = pd.DataFrame({
    'variable': X_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

# 4-3. XGBoost (GridSearch)
print("\n[4-3] XGBoost with GridSearch...")

# GPU 사용 가능 여부 확인 (더 안전한 방법)
tree_method = 'hist'  # 기본값: CPU 모드
predictor = 'cpu_predictor'  # 기본값: CPU 모드

try:
    import subprocess
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
    gpu_available = result.returncode == 0
    
    if gpu_available:
        # GPU가 감지되었어도 XGBoost GPU 지원 여부를 실제로 테스트
        try:
            test_model = xgb.XGBClassifier(
                n_estimators=1,
                tree_method='gpu_hist',
                predictor='gpu_predictor',
                random_state=42
            )
            # 작은 샘플로 테스트
            test_X = X_train[:10]
            test_y = y_train[:10]
            test_model.fit(test_X, test_y)
            print("  GPU 사용 가능 - XGBoost GPU 모드 사용")
            tree_method = 'gpu_hist'
            predictor = 'gpu_predictor'
        except Exception as e:
            print(f"  GPU 감지되었으나 XGBoost GPU 모드 사용 불가: {str(e)[:50]}")
            print("  CPU 모드로 전환")
            tree_method = 'hist'
            predictor = 'cpu_predictor'
    else:
        print("  GPU 미감지 - XGBoost CPU 모드 사용")
except Exception as e:
    print(f"  GPU 확인 실패 - XGBoost CPU 모드 사용: {str(e)[:50]}")

xgb_param_grid = {
    'n_estimators': [200, 300],
    'max_depth': [4, 6, 8],
    'learning_rate': [0.05, 0.1, 0.15],
    'subsample': [0.8, 0.9]
}

xgb_base = xgb.XGBClassifier(
    random_state=42,
    eval_metric='mlogloss',
    # use_label_encoder=False,
    tree_method=tree_method,
    # predictor=predictor
)

xgb_grid = GridSearchCV(xgb_base, xgb_param_grid, cv=5, scoring='f1_weighted', n_jobs=-1, verbose=1)
xgb_grid.fit(X_train, y_train)

xgb_model = xgb_grid.best_estimator_
y_pred_xgb = xgb_model.predict(X_test)
xgb_accuracy = accuracy_score(y_test, y_pred_xgb)
xgb_f1 = f1_score(y_test, y_pred_xgb, average='weighted')

print(f"  Best params: {xgb_grid.best_params_}")
print(f"  Accuracy: {xgb_accuracy:.4f}")
print(f"  F1-score (weighted): {xgb_f1:.4f}")

# 변수 중요도
xgb_importance = pd.DataFrame({
    'variable': X_cols,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

# ============================================================================
# 5. 교차 검증
# ============================================================================
print("\n[5] 교차 검증 수행 중...")

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

cv_scores_lr = cross_val_score(lr_model, X_train_scaled, y_train, cv=skf, scoring='f1_weighted')
cv_scores_rf = cross_val_score(rf_model, X_train, y_train, cv=skf, scoring='f1_weighted')
cv_scores_xgb = cross_val_score(xgb_model, X_train, y_train, cv=skf, scoring='f1_weighted')

print(f"  Logistic Regression CV F1: {cv_scores_lr.mean():.4f} (+/- {cv_scores_lr.std() * 2:.4f})")
print(f"  Random Forest CV F1: {cv_scores_rf.mean():.4f} (+/- {cv_scores_rf.std() * 2:.4f})")
print(f"  XGBoost CV F1: {cv_scores_xgb.mean():.4f} (+/- {cv_scores_xgb.std() * 2:.4f})")

# ============================================================================
# 6. 결과 시각화
# ============================================================================
print("\n[6] 결과 시각화 중...")

# 6-1. 모델 성능 비교
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

models = ['Logistic Regression', 'Random Forest', 'XGBoost']
accuracies = [lr_accuracy, rf_accuracy, xgb_accuracy]
f1_scores = [lr_f1, rf_f1, xgb_f1]

x = np.arange(len(models))
width = 0.35

axes[0].bar(x - width/2, accuracies, width, label='Accuracy', color='steelblue')
axes[0].bar(x + width/2, f1_scores, width, label='F1-Score', color='orange')
axes[0].set_xlabel('Model', fontsize=12)
axes[0].set_ylabel('Score', fontsize=12)
axes[0].set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(models, rotation=45, ha='right')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 6-2. 혼동행렬
fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))

for idx, (name, y_pred) in enumerate([('Logistic Regression', y_pred_lr), 
                                     ('Random Forest', y_pred_rf), 
                                     ('XGBoost', y_pred_xgb)]):
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes2[idx], cbar=False)
    axes2[idx].set_xlabel('Predicted', fontsize=11)
    axes2[idx].set_ylabel('Actual', fontsize=11)
    axes2[idx].set_title(f'{name}\nAccuracy: {accuracy_score(y_test, y_pred):.3f}', 
                        fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('results/confusion_matrices_no_outlier_removal.png', dpi=300, bbox_inches='tight')
plt.close()

# 6-3. 변수 중요도 비교
fig3, axes3 = plt.subplots(1, 2, figsize=(16, 8))

top_n = 15
rf_top = rf_importance.head(top_n)
axes3[0].barh(range(len(rf_top)), rf_top['importance'].values)
axes3[0].set_yticks(range(len(rf_top)))
axes3[0].set_yticklabels(rf_top['variable'].values, fontsize=9)
axes3[0].set_xlabel('Importance', fontsize=12)
axes3[0].set_title('Random Forest - Top 15 Feature Importance', fontsize=14, fontweight='bold')
axes3[0].invert_yaxis()

xgb_top = xgb_importance.head(top_n)
axes3[1].barh(range(len(xgb_top)), xgb_top['importance'].values, color='orange')
axes3[1].set_yticks(range(len(xgb_top)))
axes3[1].set_yticklabels(xgb_top['variable'].values, fontsize=9)
axes3[1].set_xlabel('Importance', fontsize=12)
axes3[1].set_title('XGBoost - Top 15 Feature Importance', fontsize=14, fontweight='bold')
axes3[1].invert_yaxis()

plt.tight_layout()
plt.savefig('results/feature_importance_no_outlier_removal.png', dpi=300, bbox_inches='tight')
plt.close()

print("  Saved: confusion_matrices_no_outlier_removal.png, feature_importance_no_outlier_removal.png")

# ============================================================================
# 7. 결과 저장
# ============================================================================
print("\n[7] 결과 저장 중...")

# 모델 성능 비교
performance_df = pd.DataFrame({
    'Model': ['Logistic Regression', 'Random Forest', 'XGBoost'],
    'Accuracy': [lr_accuracy, rf_accuracy, xgb_accuracy],
    'F1_Score': [lr_f1, rf_f1, xgb_f1],
    'CV_F1_Mean': [cv_scores_lr.mean(), cv_scores_rf.mean(), cv_scores_xgb.mean()],
    'CV_F1_Std': [cv_scores_lr.std(), cv_scores_rf.std(), cv_scores_xgb.std()]
})
performance_df.to_csv('results/model_performance_no_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("  Saved: model_performance_no_outlier_removal.csv")

# 변수 중요도 저장
rf_importance.to_csv('results/rf_feature_importance_no_outlier_removal.csv', index=False, encoding='utf-8-sig')
xgb_importance.to_csv('results/xgb_feature_importance_no_outlier_removal.csv', index=False, encoding='utf-8-sig')
print("  Saved: rf_feature_importance_no_outlier_removal.csv, xgb_feature_importance_no_outlier_removal.csv")

# 분류 리포트 저장
for name, y_pred in [('Logistic_Regression', y_pred_lr), 
                     ('Random_Forest', y_pred_rf), 
                     ('XGBoost', y_pred_xgb)]:
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv(f'results/classification_report_{name}_no_outlier_removal.csv', 
                     encoding='utf-8-sig')
    print(f"  Saved: classification_report_{name}_no_outlier_removal.csv")

# ============================================================================
# 8. 요약
# ============================================================================
print("\n" + "=" * 80)
print("Improved Analysis Complete! (WITHOUT Outlier Removal)_Server")
print("=" * 80)
print(f"\nModel Performance:")
print(performance_df)
print(f"\nBest Model: {models[np.argmax(accuracies)]} (Accuracy: {max(accuracies):.4f})")
print(f"\nTop 10 Feature Importance (Random Forest):")
print(rf_importance.head(10))
print(f"\nTop 10 Feature Importance (XGBoost):")
print(xgb_importance.head(10))

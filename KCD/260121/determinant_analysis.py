"""
Determinant Analysis of Small Business Lifecycle Clusters
- Multinomial Logistic Regression
- Random Forest
- XGBoost
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression
import xgboost as xgb
import warnings
warnings.filterwarnings('ignore')

# 한글 폰트 설정 (macOS)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

# Variable name mapping for better visualization labels
VARIABLE_LABELS = {
    'business_age_months': 'Business Age (Months)',
    'avg_sales_card': 'Average Sales (Card)',
    'std_sales_card': 'Sales Std Dev',
    'cv_sales_card': 'Sales Volatility (CV)',
    'growth_rate': 'Growth Rate',
    'trend_slope': 'Trend Slope',
    'weekend_ratio': 'Weekend Sales Ratio',
    'avg_customer': 'Average Customers',
    'cv_customer': 'Customer Volatility (CV)',
    'new_customer_ratio': 'New Customer Ratio',
    'card_ratio': 'Card Sales Ratio',
    'delivery_ratio': 'Delivery Sales Ratio',
    'before_noon_ratio': 'Before Noon Sales Ratio',
    'after_noon_ratio': 'After Noon Sales Ratio',
    'max_sales': 'Max Sales',
    'min_sales': 'Min Sales',
    'max_min_ratio': 'Max/Min Ratio',
    'business_square_size': 'Store Size (sqm)',
    'delivery_link': 'Delivery Available',
    'age_numeric': 'Owner Age (Numeric)',
    'dong_store_count': 'Stores in Dong',
    'dong_avg_sales': 'Avg Sales in Dong',
    'sigungu_store_count': 'Stores in Sigungu',
    'sigungu_avg_sales': 'Avg Sales in Sigungu',
    'business_density': 'Business Density',
    'sales_per_area': 'Sales per Area',
    'sales_per_customer': 'Sales per Customer',
    'total_weeks': 'Total Weeks'
}

def get_variable_label(var_name):
    """Get readable English label for variable name"""
    # Check if it's a one-hot encoded categorical variable
    if '_' in var_name and any(var_name.startswith(prefix) for prefix in ['sigungu_', 'dong_', 'depth_', 'age_']):
        # Extract the category name
        parts = var_name.split('_', 1)
        if len(parts) > 1:
            return f"{parts[0].title()} ({parts[1]})"
        return var_name.replace('_', ' ').title()
    return VARIABLE_LABELS.get(var_name, var_name.replace('_', ' ').title())

print("=" * 80)
print("Determinant Analysis of Small Business Lifecycle Clusters")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

df = pd.read_csv('store_features_for_analysis.csv')
print(f"데이터 shape: {df.shape}")
print(f"Cluster distribution:")
print(df['cluster'].value_counts().sort_index())

# ============================================================================
# 2. 데이터 전처리
# ============================================================================
print("\n[2] 데이터 전처리 중...")

# 클러스터를 정수형으로 변환
df['cluster'] = df['cluster'].astype(int)

# 분석에서 제외할 컬럼
exclude_cols = ['public_id', 'open_month', 'age', 'sigungu', 'dong', 
                'depth_1', 'depth_2', 'depth_3']

# 범주형 변수 인코딩
print("  - Encoding categorical variables...")
categorical_cols = ['sigungu', 'dong', 'depth_1', 'depth_2', 'depth_3', 'age']

# 원-핫 인코딩 (머신러닝용)
df_encoded = df.copy()
for col in categorical_cols:
    if col in df_encoded.columns:
        dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
        df_encoded = pd.concat([df_encoded, dummies], axis=1)
        df_encoded = df_encoded.drop(columns=[col])

# 숫자형 변수만 선택 (로지스틱 회귀용 - 범주형은 별도 처리)
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [col for col in numeric_cols if col not in ['cluster', 'public_id']]

# 결측치 처리
print("  - Handling missing values...")
for col in numeric_cols:
    if df[col].isna().sum() > 0:
        df[col].fillna(df[col].median(), inplace=True)
        df_encoded[col].fillna(df_encoded[col].median(), inplace=True)

# 이상치 처리 (윈저화: 상하위 1%)
print("  - Handling outliers (Winsorization)...")
for col in numeric_cols:
    if col in df.columns:
        q1 = df[col].quantile(0.01)
        q99 = df[col].quantile(0.99)
        df[col] = df[col].clip(lower=q1, upper=q99)
        df_encoded[col] = df_encoded[col].clip(lower=q1, upper=q99)

# 파생 변수 생성
print("  - Creating derived variables...")
if 'avg_sales_card' in df.columns and 'business_square_size' in df.columns:
    df['sales_per_area'] = df['avg_sales_card'] / (df['business_square_size'] + 1)
    df_encoded['sales_per_area'] = df_encoded['avg_sales_card'] / (df_encoded['business_square_size'] + 1)

if 'avg_sales_card' in df.columns and 'avg_customer' in df.columns:
    df['sales_per_customer'] = df['avg_sales_card'] / (df['avg_customer'] + 1)
    df_encoded['sales_per_customer'] = df_encoded['avg_sales_card'] / (df_encoded['avg_customer'] + 1)

# X, y 준비
print("  - X, y 준비...")
X_cols = [col for col in df_encoded.columns if col not in ['cluster', 'public_id', 'open_month']]
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
print(f"  Class distribution (training set):")
print(y_train.value_counts().sort_index())

# 스케일링 (로지스틱 회귀용)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 4. 다항 로지스틱 회귀분석
# ============================================================================
print("\n[4] 다항 로지스틱 회귀분석 수행 중...")

lr_model = LogisticRegression(
    multi_class='multinomial',
    solver='lbfgs',
    max_iter=1000,
    class_weight='balanced',
    random_state=42
)

lr_model.fit(X_train_scaled, y_train)
y_pred_lr = lr_model.predict(X_test_scaled)
y_pred_proba_lr = lr_model.predict_proba(X_test_scaled)

lr_accuracy = accuracy_score(y_test, y_pred_lr)
lr_f1 = f1_score(y_test, y_pred_lr, average='weighted')

print(f"  Accuracy: {lr_accuracy:.4f}")
print(f"  F1-score (weighted): {lr_f1:.4f}")

# 회귀계수 추출 (각 클래스별)
print("\n  Top 5 variable coefficients by class:")
coef_df_list = []
for i, class_label in enumerate(sorted(y.unique())):
    coef = lr_model.coef_[i]
    coef_df = pd.DataFrame({
        'variable': X_cols,
        'coefficient': coef,
        'class': class_label
    })
    coef_df = coef_df.reindex(coef_df['coefficient'].abs().sort_values(ascending=False).index)
    coef_df_list.append(coef_df)
    print(f"\n  Class {class_label} (vs reference class):")
    print(coef_df.head())

# ============================================================================
# 5. 랜덤 포레스트
# ============================================================================
print("\n[5] 랜덤 포레스트 모델 학습 중...")

rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=15,
    min_samples_split=10,
    min_samples_leaf=5,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

rf_model.fit(X_train, y_train)
y_pred_rf = rf_model.predict(X_test)
y_pred_proba_rf = rf_model.predict_proba(X_test)

rf_accuracy = accuracy_score(y_test, y_pred_rf)
rf_f1 = f1_score(y_test, y_pred_rf, average='weighted')

print(f"  Accuracy: {rf_accuracy:.4f}")
print(f"  F1-score (weighted): {rf_f1:.4f}")

# 변수 중요도
rf_importance = pd.DataFrame({
    'variable': X_cols,
    'importance': rf_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n  Top 10 feature importance:")
print(rf_importance.head(10))

# ============================================================================
# 6. XGBoost
# ============================================================================
print("\n[6] XGBoost 모델 학습 중...")

xgb_model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='mlogloss',
    use_label_encoder=False
)

xgb_model.fit(X_train, y_train)
y_pred_xgb = xgb_model.predict(X_test)
y_pred_proba_xgb = xgb_model.predict_proba(X_test)

xgb_accuracy = accuracy_score(y_test, y_pred_xgb)
xgb_f1 = f1_score(y_test, y_pred_xgb, average='weighted')

print(f"  Accuracy: {xgb_accuracy:.4f}")
print(f"  F1-score (weighted): {xgb_f1:.4f}")

# 변수 중요도
xgb_importance = pd.DataFrame({
    'variable': X_cols,
    'importance': xgb_model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n  Top 10 feature importance:")
print(xgb_importance.head(10))

# ============================================================================
# 7. 결과 시각화
# ============================================================================
print("\n[7] 결과 시각화 중...")

# 결과 저장 디렉토리
import os
os.makedirs('result_img/determinant_analysis', exist_ok=True)
os.makedirs('result_csv/determinant_analysis', exist_ok=True)

# 7-1. 변수 중요도 비교 (랜덤 포레스트 + XGBoost)
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# 랜덤 포레스트
top_n = 15
rf_top = rf_importance.head(top_n)
rf_labels = [get_variable_label(var) for var in rf_top['variable'].values]
axes[0].barh(range(len(rf_top)), rf_top['importance'].values)
axes[0].set_yticks(range(len(rf_top)))
axes[0].set_yticklabels(rf_labels, fontsize=9)
axes[0].set_xlabel('Importance', fontsize=12)
axes[0].set_title('Random Forest - Top 15 Feature Importance', fontsize=14, fontweight='bold')
axes[0].invert_yaxis()

# XGBoost
xgb_top = xgb_importance.head(top_n)
xgb_labels = [get_variable_label(var) for var in xgb_top['variable'].values]
axes[1].barh(range(len(xgb_top)), xgb_top['importance'].values, color='orange')
axes[1].set_yticks(range(len(xgb_top)))
axes[1].set_yticklabels(xgb_labels, fontsize=9)
axes[1].set_xlabel('Importance', fontsize=12)
axes[1].set_title('XGBoost - Top 15 Feature Importance', fontsize=14, fontweight='bold')
axes[1].invert_yaxis()

plt.tight_layout()
plt.savefig('result_img/determinant_analysis/feature_importance_comparison.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: feature_importance_comparison.png")

# 7-2. 혼동행렬
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

models = [
    ('Logistic Regression', y_pred_lr, axes[0]),
    ('Random Forest', y_pred_rf, axes[1]),
    ('XGBoost', y_pred_xgb, axes[2])
]

for name, y_pred, ax in models:
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax, cbar=False)
    ax.set_xlabel('Predicted', fontsize=11)
    ax.set_ylabel('Actual', fontsize=11)
    ax.set_title(f'{name}\nAccuracy: {accuracy_score(y_test, y_pred):.3f}', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('result_img/determinant_analysis/confusion_matrices.png', dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: confusion_matrices.png")

# 7-3. 클러스터별 분류 리포트
print("\n[8] Generating classification reports...")

for name, y_pred in [('Logistic Regression', y_pred_lr), 
                     ('Random Forest', y_pred_rf), 
                     ('XGBoost', y_pred_xgb)]:
    report = classification_report(y_test, y_pred, output_dict=True)
    report_df = pd.DataFrame(report).transpose()
    report_df.to_csv(f'result_csv/determinant_analysis/classification_report_{name.replace(" ", "_")}.csv', 
                     encoding='utf-8-sig')
    print(f"  Saved: classification_report_{name.replace(' ', '_')}.csv")

# ============================================================================
# 8. 결과 저장
# ============================================================================
print("\n[9] Saving results...")

# 모델 성능 비교
performance_df = pd.DataFrame({
    'Model': ['Logistic Regression', 'Random Forest', 'XGBoost'],
    'Accuracy': [lr_accuracy, rf_accuracy, xgb_accuracy],
    'F1_Score': [lr_f1, rf_f1, xgb_f1]
})
performance_df.to_csv('result_csv/determinant_analysis/model_performance.csv', 
                      index=False, encoding='utf-8-sig')
print("  Saved: model_performance.csv")

# 변수 중요도 저장
rf_importance.to_csv('result_csv/determinant_analysis/rf_feature_importance.csv', 
                     index=False, encoding='utf-8-sig')
xgb_importance.to_csv('result_csv/determinant_analysis/xgb_feature_importance.csv', 
                      index=False, encoding='utf-8-sig')
print("  Saved: rf_feature_importance.csv, xgb_feature_importance.csv")

# 로지스틱 회귀 계수 저장
all_coef_df = pd.concat(coef_df_list, ignore_index=True)
all_coef_df.to_csv('result_csv/determinant_analysis/logistic_regression_coefficients.csv', 
                   index=False, encoding='utf-8-sig')
print("  Saved: logistic_regression_coefficients.csv")

# ============================================================================
# 9. 요약 통계
# ============================================================================
print("\n" + "=" * 80)
print("Analysis Complete!")
print("=" * 80)
print(f"\nModel Performance:")
print(performance_df)
print(f"\nRandom Forest - Top 10 Feature Importance:")
print(rf_importance.head(10))
print(f"\nXGBoost - Top 10 Feature Importance:")
print(xgb_importance.head(10))

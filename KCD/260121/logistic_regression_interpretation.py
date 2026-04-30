"""
Logistic Regression Results Interpretation and Visualization
- Odds Ratio Interpretation
- Prediction Probability Curves
- Marginal Effects
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
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
print("Logistic Regression Results Interpretation")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드 및 준비
# ============================================================================
print("\n[1] Loading data...")

df = pd.read_csv('store_features_for_analysis.csv')
df['cluster'] = df['cluster'].astype(int)

# 범주형 변수 인코딩
categorical_cols = ['sigungu', 'dong', 'depth_1', 'depth_2', 'depth_3', 'age']
df_encoded = df.copy()
for col in categorical_cols:
    if col in df_encoded.columns:
        dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
        df_encoded = pd.concat([df_encoded, dummies], axis=1)
        df_encoded = df_encoded.drop(columns=[col])

# 숫자형 변수만 선택
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [col for col in numeric_cols if col not in ['cluster', 'public_id']]

# 결측치 및 이상치 처리
for col in numeric_cols:
    if df[col].isna().sum() > 0:
        df[col].fillna(df[col].median(), inplace=True)
        df_encoded[col].fillna(df_encoded[col].median(), inplace=True)
    q1 = df[col].quantile(0.01)
    q99 = df[col].quantile(0.99)
    df[col] = df[col].clip(lower=q1, upper=q99)
    df_encoded[col] = df_encoded[col].clip(lower=q1, upper=q99)

# 파생 변수
if 'avg_sales_card' in df.columns and 'business_square_size' in df.columns:
    df['sales_per_area'] = df['avg_sales_card'] / (df['business_square_size'] + 1)
    df_encoded['sales_per_area'] = df_encoded['avg_sales_card'] / (df_encoded['business_square_size'] + 1)

X_cols = [col for col in df_encoded.columns if col not in ['cluster', 'public_id', 'open_month']]
X = df_encoded[X_cols].copy()
y = df_encoded['cluster'].copy()

# 훈련/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 2. 로지스틱 회귀 모델 학습
# ============================================================================
print("\n[2] Training logistic regression model...")

lr_model = LogisticRegression(
    multi_class='multinomial',
    solver='lbfgs',
    max_iter=1000,
    class_weight='balanced',
    random_state=42
)

lr_model.fit(X_train_scaled, y_train)

# ============================================================================
# 3. 오즈비 계산 및 해석
# ============================================================================
print("\n[3] Calculating odds ratios...")

# 기준 클래스는 가장 많은 클래스로 설정
base_class = y_train.value_counts().index[0]
print(f"  Reference class: {base_class}")

# 각 클래스별 회귀계수 및 오즈비
odds_ratio_results = []
for i, class_label in enumerate(sorted(y.unique())):
    if class_label != base_class:
        coef = lr_model.coef_[i]
        odds_ratio = np.exp(coef)
        
        for var_idx, var_name in enumerate(X_cols):
            odds_ratio_results.append({
                'class': class_label,
                'variable': var_name,
                'coefficient': coef[var_idx],
                'odds_ratio': odds_ratio[var_idx],
                'base_class': base_class
            })

odds_df = pd.DataFrame(odds_ratio_results)
odds_df = odds_df.sort_values('odds_ratio', ascending=False, key=abs)

# 상위 변수 저장
odds_df.to_csv('result_csv/determinant_analysis/odds_ratios.csv', 
               index=False, encoding='utf-8-sig')
print("  Saved: odds_ratios.csv")

# ============================================================================
# 4. 주요 변수별 예측 확률 곡선
# ============================================================================
print("\n[4] Generating prediction probability curves for key variables...")

# 상위 중요 변수 선택 (랜덤 포레스트 결과 참고)
top_variables = ['business_age_months', 'avg_sales_card', 'growth_rate', 
                 'avg_customer', 'delivery_ratio', 'cv_sales_card']

# 원본 데이터에서 해당 변수들의 인덱스 찾기
var_indices = {}
for var in top_variables:
    if var in X_cols:
        var_indices[var] = X_cols.index(var)

# 각 변수별로 예측 확률 곡선 생성
for var_name, var_idx in var_indices.items():
    if var_name in df.columns:
        # 변수 범위 생성
        var_min = df[var_name].quantile(0.05)
        var_max = df[var_name].quantile(0.95)
        var_range = np.linspace(var_min, var_max, 100)
        
        # 다른 변수들은 평균값으로 고정
        X_pred = X_train_scaled.mean(axis=0).reshape(1, -1).repeat(100, axis=0)
        X_pred[:, var_idx] = scaler.transform(
            X_train.iloc[[0] * 100].copy()
        )[:, var_idx]
        # 실제로는 변수 범위를 직접 스케일링
        var_scaled = (var_range - X_train.iloc[:, var_idx].mean()) / X_train.iloc[:, var_idx].std()
        X_pred[:, var_idx] = var_scaled
        
        # 예측 확률 계산
        proba = lr_model.predict_proba(X_pred)
        
        # 시각화
        fig, ax = plt.subplots(figsize=(10, 6))
        for class_idx, class_label in enumerate(sorted(y.unique())):
            ax.plot(var_range, proba[:, class_idx], 
                   label=f'Cluster {class_label}', linewidth=2)
        
        ax.set_xlabel(get_variable_label(var_name), fontsize=12)
        ax.set_ylabel('Predicted Probability', fontsize=12)
        ax.set_title(f'Cluster Prediction Probability by {get_variable_label(var_name)}', 
                    fontsize=14, fontweight='bold')
        ax.legend(title='Cluster', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'result_img/determinant_analysis/probability_curve_{var_name}.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: probability_curve_{var_name}.png")

# ============================================================================
# 5. 주요 변수별 오즈비 시각화
# ============================================================================
print("\n[5] Visualizing odds ratios for key variables...")

# 각 클래스별로 상위 10개 변수의 오즈비 시각화
for class_label in sorted(y.unique()):
    if class_label != base_class:
        class_odds = odds_df[odds_df['class'] == class_label].head(10)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = ['red' if x < 1 else 'green' for x in class_odds['odds_ratio']]
        ax.barh(range(len(class_odds)), class_odds['odds_ratio'], color=colors)
        ax.axvline(x=1, color='black', linestyle='--', linewidth=1)
        ax.set_yticks(range(len(class_odds)))
        odds_labels = [get_variable_label(var) for var in class_odds['variable'].values]
        ax.set_yticklabels(odds_labels, fontsize=9)
        ax.set_xlabel('Odds Ratio', fontsize=12)
        ax.set_title(f'Cluster {class_label} vs Cluster {base_class} - Top 10 Odds Ratios', 
                    fontsize=14, fontweight='bold')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig(f'result_img/determinant_analysis/odds_ratio_cluster_{class_label}.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: odds_ratio_cluster_{class_label}.png")

print("\n" + "=" * 80)
print("Logistic Regression Interpretation Complete!")
print("=" * 80)

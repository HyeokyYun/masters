"""
생애주기 코드(code) 분류: XGBoost, Random Forest, Logistic Regression
- cluster_labels.csv (public_id, cluster, code) 사용
- store_features + 추가 시계열 특성으로 code 예측
- 분류 정확도 및 classification report 저장
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import KNNImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.linear_model import LogisticRegression
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
import warnings
warnings.filterwarnings('ignore')

# 경로 (26-1 기준)
BASE = '/Volumes/SAMSUMG_128/master_graduate/KCD_source_code_from_Yang/26-1'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, 'result_csv', 'code_classification')
os.makedirs(RESULTS_DIR, exist_ok=True)

plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

print("=" * 80)
print("생애주기 코드(code) 분류: XGBoost, RF, LR")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] 데이터 로드 중...")

cluster_labels = pd.read_csv(os.path.join(BASE, '260121', 'result_csv', 'cluster_labels.csv'))
print(f"  cluster_labels.csv: {cluster_labels.shape}, columns: {list(cluster_labels.columns)}")

# code 컬럼명 통일 (생애주기_코드 -> code)
if '생애주기_코드' in cluster_labels.columns and 'code' not in cluster_labels.columns:
    cluster_labels['code'] = cluster_labels['생애주기_코드']
if 'code' not in cluster_labels.columns:
    raise ValueError("cluster_labels에 'code' 또는 '생애주기_코드' 컬럼이 필요합니다.")

store_features = pd.read_csv(os.path.join(BASE, 'basic_data', 'store_features_for_analysis.csv'))
print(f"  store_features_for_analysis.csv: {store_features.shape}")

# cluster 제거 후 라벨(코드)만 병합
if 'cluster' in store_features.columns:
    store_features = store_features.drop(columns=['cluster'])
labels_for_merge = cluster_labels[['public_id', 'code']].drop_duplicates()
df = store_features.merge(labels_for_merge, on='public_id', how='inner')
print(f"  병합 후 (public_id 기준): {df.shape}")
print(f"  code 분포:\n{df['code'].value_counts().sort_index()}")

# 추가 시계열 특성용 원본 데이터
weekly_df = pd.read_parquet(os.path.join(BASE, 'original_data', 'weekly_processed.parquet'))
weekly_df = weekly_df[weekly_df['day_after1'] != 0]
meta_df = pd.read_csv(os.path.join(BASE, 'original_data', 'meta_processed.csv'))

# ============================================================================
# 2. 추가 시계열 특성 추출 (final_determinant_analysis와 동일)
# ============================================================================
print("\n[2] 추가 시계열 특성 추출 중...")

def extract_additional_features(weekly_df, meta_df):
    features_list = []
    for public_id in weekly_df['public_id'].unique():
        store_data = weekly_df[weekly_df['public_id'] == public_id].sort_values('day_after1')
        if len(store_data) < 10:
            continue
        total_weeks = len(store_data)
        sales_values = store_data['sales_card'].values
        overall_avg = sales_values.mean()

        recent_4w_growth = recent_8w_growth = recent_12w_growth = 0
        recent_4w_avg = recent_8w_avg = recent_12w_avg = 0
        if len(sales_values) >= 4:
            recent_4w_avg = sales_values[-4:].mean()
            prev_4w_avg = sales_values[-8:-4].mean() if len(sales_values) >= 8 else sales_values[:-4].mean()
            recent_4w_growth = (recent_4w_avg - prev_4w_avg) / (prev_4w_avg + 1e-6)
        if len(sales_values) >= 8:
            recent_8w_avg = sales_values[-8:].mean()
            prev_8w_avg = sales_values[-16:-8].mean() if len(sales_values) >= 16 else sales_values[:-8].mean()
            recent_8w_growth = (recent_8w_avg - prev_8w_avg) / (prev_8w_avg + 1e-6)
        if len(sales_values) >= 12:
            recent_12w_avg = sales_values[-12:].mean()
            prev_12w_avg = sales_values[-24:-12].mean() if len(sales_values) >= 24 else sales_values[:-12].mean()
            recent_12w_growth = (recent_12w_avg - prev_12w_avg) / (prev_12w_avg + 1e-6)

        recent_4w_cv = sales_values[-4:].std() / (sales_values[-4:].mean() + 1e-6) if len(sales_values) >= 4 else 0
        recent_8w_cv = sales_values[-8:].std() / (sales_values[-8:].mean() + 1e-6) if len(sales_values) >= 8 else 0
        recent_4w_performance = recent_4w_avg / (overall_avg + 1e-6) if len(sales_values) >= 4 else 1.0
        recent_8w_performance = recent_8w_avg / (overall_avg + 1e-6) if len(sales_values) >= 8 else 1.0

        early_4w_growth = early_8w_growth = early_12w_growth = 0
        early_4w_avg = early_8w_avg = early_12w_avg = 0
        if len(sales_values) >= 8:
            early_4w_avg = sales_values[:4].mean()
            next_4w_avg = sales_values[4:8].mean()
            early_4w_growth = (next_4w_avg - early_4w_avg) / (early_4w_avg + 1e-6)
        if len(sales_values) >= 16:
            early_8w_avg = sales_values[:8].mean()
            next_8w_avg = sales_values[8:16].mean()
            early_8w_growth = (next_8w_avg - early_8w_avg) / (early_8w_avg + 1e-6)
        if len(sales_values) >= 24:
            early_12w_avg = sales_values[:12].mean()
            next_12w_avg = sales_values[12:24].mean()
            early_12w_growth = (next_12w_avg - early_12w_avg) / (early_12w_avg + 1e-6)

        early_4w_cv = sales_values[:4].std() / (sales_values[:4].mean() + 1e-6) if len(sales_values) >= 4 else 0
        early_8w_cv = sales_values[:8].std() / (sales_values[:8].mean() + 1e-6) if len(sales_values) >= 8 else 0
        early_4w_performance = early_4w_avg / (overall_avg + 1e-6) if early_4w_avg > 0 and len(sales_values) >= 4 else 1.0
        early_8w_performance = early_8w_avg / (overall_avg + 1e-6) if early_8w_avg > 0 and len(sales_values) >= 8 else 1.0

        trend_ratio = early_trend_ratio = 0
        if len(sales_values) >= 12:
            x_recent = np.arange(12)
            y_recent = sales_values[-12:]
            trend_recent = np.polyfit(x_recent, y_recent, 1)[0] if len(y_recent) > 1 else 0
            x_all = np.arange(len(sales_values))
            trend_all = np.polyfit(x_all, sales_values, 1)[0] if len(sales_values) > 1 else 0
            trend_ratio = trend_recent / (abs(trend_all) + 1e-6)
            y_early = sales_values[:12]
            trend_early = np.polyfit(x_recent, y_early, 1)[0] if len(y_early) > 1 else 0
            early_trend_ratio = trend_early / (abs(trend_all) + 1e-6)

        change_ratio = 0
        if len(sales_values) >= 8:
            diff = np.diff(sales_values[-8:])
            change_ratio = np.sum(diff > 0) / (len(diff) + 1e-6)

        features_list.append({
            'public_id': public_id,
            'recent_4w_growth': recent_4w_growth, 'recent_8w_growth': recent_8w_growth, 'recent_12w_growth': recent_12w_growth,
            'recent_4w_cv': recent_4w_cv, 'recent_8w_cv': recent_8w_cv,
            'recent_4w_performance': recent_4w_performance, 'recent_8w_performance': recent_8w_performance,
            'early_4w_growth': early_4w_growth, 'early_8w_growth': early_8w_growth, 'early_12w_growth': early_12w_growth,
            'early_4w_cv': early_4w_cv, 'early_8w_cv': early_8w_cv,
            'early_4w_performance': early_4w_performance, 'early_8w_performance': early_8w_performance,
            'trend_ratio': trend_ratio, 'early_trend_ratio': early_trend_ratio, 'change_ratio': change_ratio
        })
    return pd.DataFrame(features_list)

additional_features = extract_additional_features(weekly_df, meta_df)
df = df.merge(additional_features, on='public_id', how='left')

additional_feature_cols = [
    'recent_4w_growth', 'recent_8w_growth', 'recent_12w_growth',
    'recent_4w_cv', 'recent_8w_cv', 'recent_4w_performance', 'recent_8w_performance',
    'early_4w_growth', 'early_8w_growth', 'early_12w_growth',
    'early_4w_cv', 'early_8w_cv', 'early_4w_performance', 'early_8w_performance',
    'trend_ratio', 'early_trend_ratio', 'change_ratio'
]
for col in additional_feature_cols:
    if col in df.columns:
        df[col] = df[col].fillna(0)

# 파생 변수
if 'avg_sales_card' in df.columns and 'business_square_size' in df.columns:
    df['sales_per_area'] = df['avg_sales_card'] / (df['business_square_size'] + 1)
if 'avg_sales_card' in df.columns and 'avg_customer' in df.columns:
    df['sales_per_customer'] = df['avg_sales_card'] / (df['avg_customer'] + 1)
if 'early_4w_growth' in df.columns and 'recent_4w_growth' in df.columns:
    df['growth_change_4w'] = df['recent_4w_growth'] - df['early_4w_growth']
    df['growth_change_8w'] = df.get('recent_8w_growth', 0) - df.get('early_8w_growth', 0)
if 'early_4w_cv' in df.columns and 'recent_4w_cv' in df.columns:
    df['cv_change_4w'] = df['recent_4w_cv'] - df['early_4w_cv']
    df['cv_change_8w'] = df.get('recent_8w_cv', 0) - df.get('early_8w_cv', 0)
if 'early_4w_performance' in df.columns and 'recent_4w_performance' in df.columns:
    df['performance_change_4w'] = df['recent_4w_performance'] - df['early_4w_performance']
    df['performance_change_8w'] = df.get('recent_8w_performance', 0) - df.get('early_8w_performance', 0)

# 범주형 인코딩 (지역 제외)
categorical_cols = ['depth_1', 'depth_2', 'depth_3', 'age']
df_encoded = df.copy()
for col in categorical_cols:
    if col in df_encoded.columns:
        dummies = pd.get_dummies(df_encoded[col], prefix=col, drop_first=True)
        df_encoded = pd.concat([df_encoded, dummies], axis=1)
        df_encoded = df_encoded.drop(columns=[col])
for drop_col in ['dong', 'sigungu']:
    if drop_col in df_encoded.columns:
        df_encoded = df_encoded.drop(columns=[drop_col])

numeric_cols = df_encoded.select_dtypes(include=[np.number]).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ['public_id', 'total_weeks']]

# KNN Imputation
imputer = KNNImputer(n_neighbors=5)
df_encoded[numeric_cols] = imputer.fit_transform(df_encoded[numeric_cols])

# Winsorization
for col in numeric_cols:
    if col in df_encoded.columns:
        q0_5 = df_encoded[col].quantile(0.005)
        q99_5 = df_encoded[col].quantile(0.995)
        df_encoded[col] = df_encoded[col].clip(lower=q0_5, upper=q99_5)

# X, y (목표: code)
exclude_cols = ['code', 'cluster', 'public_id', 'open_month', 'total_weeks']
X_cols = [c for c in df_encoded.columns if c not in exclude_cols]
X_cols = [c for c in X_cols if not c.startswith('dong_') and not c.startswith('sigungu_')]

X = df_encoded[X_cols].copy()
y = df_encoded['code'].astype(str).copy()

# 특성 선택
variance_selector = VarianceThreshold(threshold=0.01)
variance_selector.fit(X)
selected_variance = X.columns[variance_selector.get_support()].tolist()
if len(selected_variance) > 200:
    k_best = SelectKBest(f_classif, k=200)
    X_temp = X[selected_variance].copy()
    k_best.fit(X_temp, y)
    X_cols = X_temp.columns[k_best.get_support()].tolist()
    X = X[X_cols].copy()
else:
    X_cols = selected_variance
    X = X[X_cols].copy()

print(f"  최종 특성 수: {len(X_cols)}, 샘플 수: {len(X)}")

# 코드 문자열 -> 정수 (XGBoost 등 정수 레이블 필요)
label_encoder = LabelEncoder()
y_enc = label_encoder.fit_transform(y)  # DDY, DDZ, ... -> 0, 1, 2, ...
codes = list(label_encoder.classes_)   # 보고용 코드 순서

# ============================================================================
# 3. 훈련/테스트 분할
# ============================================================================
print("\n[3] 훈련/테스트 분할 (stratify=code)...")

X_train, X_test, y_train_enc, y_test_enc = train_test_split(
    X, y_enc, test_size=0.3, random_state=42, stratify=y_enc
)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 4. 모델 학습 (XGBoost, RF, LR)
# ============================================================================
print("\n[4] 모델 학습 중...")

# 4-1. Logistic Regression (정수 레이블 사용)
lr_base = LogisticRegression(solver='lbfgs', class_weight='balanced', max_iter=3000, random_state=42)
lr_grid = GridSearchCV(lr_base, {'C': [0.1, 1, 10], 'max_iter': [2000, 3000]}, cv=5, scoring='f1_weighted', n_jobs=1)
lr_grid.fit(X_train_scaled, y_train_enc)
lr_model = lr_grid.best_estimator_
y_pred_lr_enc = lr_model.predict(X_test_scaled)
y_pred_lr = label_encoder.inverse_transform(y_pred_lr_enc)
lr_acc = accuracy_score(y_test_enc, y_pred_lr_enc)
lr_f1 = f1_score(y_test_enc, y_pred_lr_enc, average='weighted')
print(f"  Logistic Regression - Accuracy: {lr_acc:.4f}, F1(weighted): {lr_f1:.4f}")

# 4-2. Random Forest
rf_base = RandomForestClassifier(class_weight='balanced', random_state=42, n_jobs=1)
rf_grid = GridSearchCV(rf_base, {'n_estimators': [200, 300], 'max_depth': [15, 20], 'min_samples_split': [5, 10]}, cv=5, scoring='f1_weighted', n_jobs=1)
rf_grid.fit(X_train, y_train_enc)
rf_model = rf_grid.best_estimator_
y_pred_rf_enc = rf_model.predict(X_test)
y_pred_rf = label_encoder.inverse_transform(y_pred_rf_enc)
rf_acc = accuracy_score(y_test_enc, y_pred_rf_enc)
rf_f1 = f1_score(y_test_enc, y_pred_rf_enc, average='weighted')
print(f"  Random Forest - Accuracy: {rf_acc:.4f}, F1(weighted): {rf_f1:.4f}")

# 4-3. XGBoost (정수 레이블 필수)
xgb_model = None
y_pred_xgb = None
xgb_acc = xgb_f1 = None
if HAS_XGB:
    tree_method = 'hist'
    try:
        import subprocess
        r = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            try:
                t = xgb.XGBClassifier(n_estimators=1, tree_method='gpu_hist', random_state=42)
                t.fit(X_train.head(10), y_train_enc[:10])
                tree_method = 'gpu_hist'
            except Exception:
                pass
    except Exception:
        pass
    xgb_base = xgb.XGBClassifier(random_state=42, eval_metric='mlogloss', tree_method=tree_method)
    xgb_grid = GridSearchCV(xgb_base, {'n_estimators': [200, 300], 'max_depth': [6, 8], 'learning_rate': [0.05, 0.1]}, cv=5, scoring='f1_weighted', n_jobs=1)
    xgb_grid.fit(X_train, y_train_enc)
    xgb_model = xgb_grid.best_estimator_
    y_pred_xgb_enc = xgb_model.predict(X_test)
    y_pred_xgb = label_encoder.inverse_transform(y_pred_xgb_enc)
    xgb_acc = accuracy_score(y_test_enc, y_pred_xgb_enc)
    xgb_f1 = f1_score(y_test_enc, y_pred_xgb_enc, average='weighted')
    print(f"  XGBoost - Accuracy: {xgb_acc:.4f}, F1(weighted): {xgb_f1:.4f}")
else:
    print("  XGBoost - skipped (xgboost not installed)")

# ============================================================================
# 5. 교차 검증
# ============================================================================
print("\n[5] 5-Fold 교차 검증...")
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_lr = cross_val_score(lr_model, X_train_scaled, y_train_enc, cv=skf, scoring='f1_weighted')
cv_rf = cross_val_score(rf_model, X_train, y_train_enc, cv=skf, scoring='f1_weighted')
cv_xgb = cross_val_score(xgb_model, X_train, y_train_enc, cv=skf, scoring='f1_weighted') if HAS_XGB and xgb_model is not None else np.array([np.nan])
print(f"  LR   CV F1: {cv_lr.mean():.4f} (+/- {cv_lr.std()*2:.4f})")
print(f"  RF   CV F1: {cv_rf.mean():.4f} (+/- {cv_rf.std()*2:.4f})")
if HAS_XGB and xgb_model is not None:
    print(f"  XGB  CV F1: {cv_xgb.mean():.4f} (+/- {cv_xgb.std()*2:.4f})")

# ============================================================================
# 6. 결과 저장
# ============================================================================
print("\n[6] 결과 저장 중...")

# 모델별 정확도 요약
_perf = [{'Model': 'Logistic Regression', 'Accuracy': lr_acc, 'F1_Score_weighted': lr_f1, 'CV_F1_Mean': cv_lr.mean(), 'CV_F1_Std': cv_lr.std()},
         {'Model': 'Random Forest', 'Accuracy': rf_acc, 'F1_Score_weighted': rf_f1, 'CV_F1_Mean': cv_rf.mean(), 'CV_F1_Std': cv_rf.std()}]
if HAS_XGB and xgb_model is not None:
    _perf.append({'Model': 'XGBoost', 'Accuracy': xgb_acc, 'F1_Score_weighted': xgb_f1, 'CV_F1_Mean': cv_xgb.mean(), 'CV_F1_Std': cv_xgb.std()})
performance_df = pd.DataFrame(_perf)
performance_df.to_csv(os.path.join(RESULTS_DIR, 'model_performance_code.csv'), index=False, encoding='utf-8-sig')
print(f"  Saved: {RESULTS_DIR}/model_performance_code.csv")

# Classification report (code 문자열로 저장)
y_test_codes = label_encoder.inverse_transform(y_test_enc)
_reports = [('Logistic_Regression', y_pred_lr), ('Random_Forest', y_pred_rf)]
if HAS_XGB and y_pred_xgb is not None:
    _reports.append(('XGBoost', y_pred_xgb))
for name, y_pred in _reports:
    report = classification_report(y_test_codes, y_pred, output_dict=True)
    pd.DataFrame(report).transpose().to_csv(
        os.path.join(RESULTS_DIR, f'classification_report_code_{name}.csv'), encoding='utf-8-sig'
    )
    print(f"  Saved: classification_report_code_{name}.csv")

# 혼동 행렬 시각화 (코드 문자열)
n_models = 3 if (HAS_XGB and y_pred_xgb is not None) else 2
fig, axes = plt.subplots(1, n_models, figsize=(6 * n_models, 5))
if n_models == 2:
    axes = [axes[0], axes[1]]
_plots = [('Logistic Regression', y_pred_lr), ('Random Forest', y_pred_rf)]
if HAS_XGB and y_pred_xgb is not None:
    _plots.append(('XGBoost', y_pred_xgb))
for idx, (name, y_pred) in enumerate(_plots):
    cm = confusion_matrix(y_test_codes, y_pred, labels=codes)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx], xticklabels=codes, yticklabels=codes)
    axes[idx].set_xlabel('Predicted (code)')
    axes[idx].set_ylabel('Actual (code)')
    axes[idx].set_title(f'{name}\nAccuracy: {accuracy_score(y_test_codes, y_pred):.3f}')
plt.tight_layout()
plt.savefig(os.path.join(RESULTS_DIR, 'confusion_matrices_code.png'), dpi=150, bbox_inches='tight')
plt.close()
print("  Saved: confusion_matrices_code.png")

# Feature importance (RF, XGB)
rf_imp = pd.DataFrame({'variable': X_cols, 'importance': rf_model.feature_importances_}).sort_values('importance', ascending=False)
rf_imp.to_csv(os.path.join(RESULTS_DIR, 'rf_feature_importance_code.csv'), index=False, encoding='utf-8-sig')
if HAS_XGB and xgb_model is not None:
    xgb_imp = pd.DataFrame({'variable': X_cols, 'importance': xgb_model.feature_importances_}).sort_values('importance', ascending=False)
    xgb_imp.to_csv(os.path.join(RESULTS_DIR, 'xgb_feature_importance_code.csv'), index=False, encoding='utf-8-sig')
print("  Saved: rf_feature_importance_code.csv" + (", xgb_feature_importance_code.csv" if HAS_XGB and xgb_model else ""))

# ============================================================================
# 7. 요약 출력
# ============================================================================
print("\n" + "=" * 80)
print("생애주기 코드(code) 분류 결과 요약")
print("=" * 80)
print(performance_df.to_string(index=False))
print("\nBest Accuracy:", performance_df.loc[performance_df['Accuracy'].idxmax(), 'Model'], f"({performance_df['Accuracy'].max():.4f})")
print("결과 디렉토리:", RESULTS_DIR)
print("=" * 80)

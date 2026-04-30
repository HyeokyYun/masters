"""
Cluster Descriptive Statistics and Exploratory Analysis
- Cluster summary statistics by variables
- Cluster sales trend visualization
- Cluster characteristics comparison
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
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
    return VARIABLE_LABELS.get(var_name, var_name.replace('_', ' ').title())

print("=" * 80)
print("Cluster Descriptive Statistics and Exploratory Analysis")
print("=" * 80)

# ============================================================================
# 1. 데이터 로드
# ============================================================================
print("\n[1] Loading data...")

df = pd.read_csv('store_features_for_analysis.csv')
df['cluster'] = df['cluster'].astype(int)

print(f"Data shape: {df.shape}")
print(f"Cluster distribution:")
cluster_counts = df['cluster'].value_counts().sort_index()
print(cluster_counts)

# ============================================================================
# 2. 군집별 기술통계
# ============================================================================
print("\n[2] Generating cluster summary statistics...")

# 주요 변수 선택
key_variables = [
    'business_age_months',  # Business age
    'avg_sales_card',  # Average sales
    'cv_sales_card',  # Sales volatility
    'growth_rate',  # Growth rate
    'trend_slope',  # Trend
    'weekend_ratio',  # Weekend sales ratio
    'avg_customer',  # Average customers
    'new_customer_ratio',  # New customer ratio
    'delivery_ratio',  # Delivery sales ratio
    'business_square_size',  # Store size
    'dong_store_count',  # Number of stores in dong
    'sigungu_avg_sales',  # Average sales in sigungu
    'business_density'  # Business density
]

# 군집별 요약 통계
summary_stats = []
for cluster_id in sorted(df['cluster'].unique()):
    cluster_data = df[df['cluster'] == cluster_id]
    stats_dict = {'cluster': cluster_id, 'n': len(cluster_data)}
    
    for var in key_variables:
        if var in cluster_data.columns:
            stats_dict[f'{var}_mean'] = cluster_data[var].mean()
            stats_dict[f'{var}_std'] = cluster_data[var].std()
            stats_dict[f'{var}_median'] = cluster_data[var].median()
    
    summary_stats.append(stats_dict)

summary_df = pd.DataFrame(summary_stats)
summary_df.to_csv('result_csv/determinant_analysis/cluster_summary_statistics.csv', 
                  index=False, encoding='utf-8-sig')
print("  Saved: cluster_summary_statistics.csv")

# ============================================================================
# 3. 군집별 변수 비교 (ANOVA)
# ============================================================================
print("\n[3] Performing ANOVA test for cluster differences...")

anova_results = []
for var in key_variables:
    if var in df.columns:
        groups = [df[df['cluster'] == c][var].dropna() for c in sorted(df['cluster'].unique())]
        groups = [g for g in groups if len(g) > 0]  # 빈 그룹 제거
        
        if len(groups) > 1:
            f_stat, p_value = stats.f_oneway(*groups)
            anova_results.append({
                'variable': var,
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': 'Yes' if p_value < 0.05 else 'No'
            })

anova_df = pd.DataFrame(anova_results)
anova_df = anova_df.sort_values('p_value')
anova_df.to_csv('result_csv/determinant_analysis/anova_results.csv', 
                index=False, encoding='utf-8-sig')
print("  Saved: anova_results.csv")
print(f"\n  Significant variables (p < 0.05): {anova_df[anova_df['significant'] == 'Yes'].shape[0]}")

# ============================================================================
# 4. 군집별 변수 비교 시각화
# ============================================================================
print("\n[4] Visualizing cluster variable comparison...")

# 주요 변수 6개 선택
top_vars = ['business_age_months', 'avg_sales_card', 'growth_rate', 
            'avg_customer', 'delivery_ratio', 'business_square_size']

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
axes = axes.flatten()

for idx, var in enumerate(top_vars):
    if var in df.columns:
        # 박스플롯
        data_to_plot = [df[df['cluster'] == c][var].dropna() 
                        for c in sorted(df['cluster'].unique())]
        axes[idx].boxplot(data_to_plot, labels=sorted(df['cluster'].unique()))
        axes[idx].set_xlabel('Cluster', fontsize=11)
        axes[idx].set_ylabel(get_variable_label(var), fontsize=11)
        axes[idx].set_title(f'{get_variable_label(var)} by Cluster', fontsize=12, fontweight='bold')
        axes[idx].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('result_img/determinant_analysis/cluster_variable_comparison.png', 
            dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: cluster_variable_comparison.png")

# ============================================================================
# 5. 군집별 평균값 히트맵
# ============================================================================
print("\n[5] Generating cluster average heatmap...")

# 주요 변수들의 군집별 평균
heatmap_data = []
for var in key_variables:
    if var in df.columns:
        row = {'variable': var}
        for cluster_id in sorted(df['cluster'].unique()):
            cluster_mean = df[df['cluster'] == cluster_id][var].mean()
            row[f'Cluster_{cluster_id}'] = cluster_mean
        heatmap_data.append(row)

heatmap_df = pd.DataFrame(heatmap_data)
heatmap_df = heatmap_df.set_index('variable')

# 정규화 (각 변수별로)
heatmap_normalized = heatmap_df.apply(lambda x: (x - x.min()) / (x.max() - x.min()), axis=1)

# 변수명을 읽기 쉬운 레이블로 변경
heatmap_normalized.index = [get_variable_label(var) for var in heatmap_normalized.index]

plt.figure(figsize=(12, 10))
sns.heatmap(heatmap_normalized, annot=True, fmt='.2f', cmap='RdYlGn', 
            cbar_kws={'label': 'Normalized Value'}, linewidths=0.5)
plt.title('Cluster Average Values Heatmap (Normalized)', fontsize=14, fontweight='bold', pad=20)
plt.xlabel('Cluster', fontsize=12)
plt.ylabel('Variable', fontsize=12)
plt.tight_layout()
plt.savefig('result_img/determinant_analysis/cluster_heatmap.png', 
            dpi=300, bbox_inches='tight')
plt.close()
print("  Saved: cluster_heatmap.png")

# ============================================================================
# 6. 군집별 업종 분포
# ============================================================================
print("\n[6] Analyzing cluster business type distribution...")

if 'depth_1' in df.columns:
    # 군집별 업종 대분류 분포
    cluster_business = pd.crosstab(df['cluster'], df['depth_1'], normalize='index') * 100
    cluster_business.to_csv('result_csv/determinant_analysis/cluster_business_distribution.csv', 
                           encoding='utf-8-sig')
    print("  Saved: cluster_business_distribution.csv")
    
    # 시각화
    plt.figure(figsize=(14, 8))
    cluster_business.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.title('Cluster Business Type Distribution', fontsize=14, fontweight='bold')
    plt.xlabel('Cluster', fontsize=12)
    plt.ylabel('Percentage (%)', fontsize=12)
    plt.legend(title='Business Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('result_img/determinant_analysis/cluster_business_distribution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved: cluster_business_distribution.png")

# ============================================================================
# 7. 군집별 지역 분포
# ============================================================================
print("\n[7] Analyzing cluster region distribution...")

if 'sigungu' in df.columns:
    # 군집별 시군구 분포
    cluster_region = pd.crosstab(df['cluster'], df['sigungu'], normalize='index') * 100
    # 상위 5개 시군구만 선택
    top_sigungu = df['sigungu'].value_counts().head(5).index
    cluster_region_top = cluster_region[top_sigungu]
    cluster_region_top.to_csv('result_csv/determinant_analysis/cluster_region_distribution.csv', 
                              encoding='utf-8-sig')
    print("  Saved: cluster_region_distribution.csv")
    
    # 시각화
    plt.figure(figsize=(12, 8))
    cluster_region_top.plot(kind='bar', ax=plt.gca())
    plt.title('Cluster Region Distribution (Top 5)', fontsize=14, fontweight='bold')
    plt.xlabel('Cluster', fontsize=12)
    plt.ylabel('Percentage (%)', fontsize=12)
    plt.legend(title='Region', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig('result_img/determinant_analysis/cluster_region_distribution.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("  Saved: cluster_region_distribution.png")

print("\n" + "=" * 80)
print("Cluster Descriptive Analysis Complete!")
print("=" * 80)

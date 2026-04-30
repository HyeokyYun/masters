"""
소상공인 생애주기 군집 결정요인 분석 - 전체 실행 스크립트
"""

import subprocess
import sys
import os

print("=" * 80)
print("소상공인 생애주기 군집 결정요인 분석 - 전체 실행")
print("=" * 80)

# 결과 디렉토리 생성
os.makedirs('result_img/determinant_analysis', exist_ok=True)
os.makedirs('result_csv/determinant_analysis', exist_ok=True)

scripts = [
    ('cluster_descriptive_analysis.py', '군집별 기술통계 분석'),
    ('determinant_analysis.py', '결정요인 분석 (로지스틱, RF, XGBoost)'),
    ('logistic_regression_interpretation.py', '로지스틱 회귀 해석')
]

for script, description in scripts:
    print(f"\n{'='*80}")
    print(f"실행 중: {description}")
    print(f"스크립트: {script}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script],
            check=True,
            capture_output=False
        )
        print(f"\n✓ {description} 완료!")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} 실패!")
        print(f"에러 코드: {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n✗ 스크립트를 찾을 수 없습니다: {script}")
        sys.exit(1)

print("\n" + "=" * 80)
print("전체 분석 완료!")
print("=" * 80)
print("\n생성된 결과 파일:")
print("  - result_csv/determinant_analysis/")
print("  - result_img/determinant_analysis/")

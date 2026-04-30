"""
논문 작성용 핵심 결과 파일을 260216/outputs 로 복사.
Run from 260216: python scripts/copy_thesis_results.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.parent

COPY_LIST = [
    # (소스, 260216 내 상대경로)
    (PROJECT / "260204/outputs/tables/compare_methods_no_dtw.csv", "tables/compare_methods_no_dtw.csv"),
    (PROJECT / "260204/outputs/tables/cluster_stability_summary.csv", "tables/cluster_stability_summary.csv"),
    (PROJECT / "260204/outputs/tables/success_rate_by_cluster.csv", "tables/success_rate_by_cluster.csv"),
    (PROJECT / "260204/outputs/tables/ablation_results.csv", "tables/ablation_results.csv"),
    (PROJECT / "260211/outputs/tables/prediction_80_20_results.csv", "tables/prediction_80_20_results.csv"),
    (PROJECT / "260204/outputs/figures/cluster_means_K6.png", "figures/cluster_means_K6.png"),
    (PROJECT / "260211/outputs/figures/prediction_80_20_M0_vs_M1.png", "figures/prediction_80_20_M0_vs_M1.png"),
]

def main():
    out_dir = ROOT / "outputs"
    for src, rel in COPY_LIST:
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            import shutil
            shutil.copy2(src, dst)
            print(f"Copied: {rel}")
        else:
            print(f"Skip (not found): {src}")

if __name__ == "__main__":
    main()

"""
클러스터 시각적 패턴 → 성장(X), 안정(Y), 퇴로(Z) 매핑 후
P1_label + P2_label + Pattern_label 로 3자리 final_code 생성 및 분포 시각화.

Run from 260204_gem: python scripts/run_02_final_code.py
"""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"
LOG_PATH = ROOT / "outputs" / "logs" / "run_02_final_code.log"

# 클러스터 시계열 시각 패턴 기준 매핑 (Cluster 0~5 → X/Y/Z)
# Cluster 0: 초기 상승 후 지속 하락 → 퇴로(Z)
# Cluster 1: 전 구간 평탄·안정 → 안정(Y)
# Cluster 2: 지속적 하락 → 퇴로(Z)
# Cluster 3: 급격한 초기 하락 후 저점 안정 → 퇴로(Z)
# Cluster 4: 뚜렷한 성장 후 고점 안정 → 성장(X)
# Cluster 5: 완만한 지속 상승 → 성장(X)
CLUSTER_TO_PATTERN = {
    0: "Z",  # Decline
    1: "Y",  # Stable
    2: "Z",  # Decline
    3: "Z",  # Decline
    4: "X",  # Growth
    5: "X",  # Growth
}


def main():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"{datetime.now().isoformat()} {msg}\n"
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print(msg)

    # 경로: 260204_gem 기준
    inflection_path = TABLES_DIR / "inflection_p1p2_labels.csv"
    cluster_path = ROOT / ".." / "260204" / "outputs" / "tables" / "store_cluster_labels_K6.parquet"
    cluster_path = cluster_path.resolve()

    if not inflection_path.exists():
        log(f"ERROR: Not found {inflection_path}. Run run_01_inflection_p1p2.py first.")
        return
    if not cluster_path.exists():
        log(f"ERROR: Not found {cluster_path}. Need 260204 K=6 cluster labels.")
        return

    log("Loading inflection P1/P2 labels and cluster labels.")
    inflection = pd.read_csv(inflection_path)
    clusters = pd.read_parquet(cluster_path)
    clusters["cluster"] = clusters["cluster"].astype(int)

    # Pattern_label: 클러스터 → X/Y/Z
    clusters["Pattern_label"] = clusters["cluster"].map(CLUSTER_TO_PATTERN)
    merged = inflection.merge(
        clusters[["public_id", "cluster", "Pattern_label"]],
        on="public_id",
        how="inner",
    )
    merged["final_code"] = (
        merged["P1_label"].astype(str)
        + merged["P2_label"].astype(str)
        + merged["Pattern_label"].astype(str)
    )

    out_table = TABLES_DIR / "final_code_by_store.csv"
    merged.to_csv(out_table, index=False, encoding="utf-8-sig")
    log(f"Saved {out_table} (rows={len(merged)})")

    # 3자리 코드 분포 막대그래프
    counts = merged["final_code"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(14, 5))
    x = range(len(counts))
    bars = ax.bar(x, counts.values, color="steelblue", edgecolor="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(counts.index, rotation=45, ha="right")
    ax.set_ylabel("Store count")
    ax.set_xlabel("Final code (P1 + P2 + Pattern)")
    ax.set_title("Final code distribution (U/D + U/D + X/Y/Z)")
    plt.tight_layout()
    fig.savefig(FIGURES_DIR / "final_code_distribution.png", bbox_inches="tight", dpi=150)
    plt.close()
    log(f"Saved {FIGURES_DIR / 'final_code_distribution.png'}")

    log("Distribution summary:")
    for code, n in counts.items():
        log(f"  {code}: {n}")
    log("Done.")


if __name__ == "__main__":
    main()

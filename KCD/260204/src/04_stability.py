"""Stability analysis for cluster assignments (e.g. repeated runs, metrics)."""
import numpy as np


def cluster_stability_score(labels_list: list[np.ndarray]) -> float:
    """Compute a simple stability score across multiple label runs (e.g. ARI or agreement)."""
    if len(labels_list) < 2:
        return 1.0
    from sklearn.metrics import adjusted_rand_score
    n = len(labels_list)
    total = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += adjusted_rand_score(labels_list[i], labels_list[j])
            count += 1
    return total / count if count else 1.0

"""Clustering utilities (e.g. KMeans on feature matrix)."""
import numpy as np
from sklearn.cluster import KMeans


def fit_kmeans(X: np.ndarray, n_clusters: int, random_state: int = 42) -> tuple:
    """Fit KMeans and return (model, labels). X must be dense numpy array."""
    if hasattr(X, "toarray"):
        X = X.toarray()
    X = np.asarray(X, dtype=float)
    km = KMeans(n_clusters=n_clusters, random_state=random_state)
    labels = km.fit_predict(X)
    return km, labels

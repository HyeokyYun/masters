"""Project 260204: helper imports (use importlib for numeric-prefix module names)."""
import importlib

_mods = (
    "00_utils",
    "01_features_data",
    "02_weekly_data",
    "03_clustering",
    "04_stability",
    "06_regression",
    "07_prediction",
    "08_artifacts",
)
for _m in _mods:
    importlib.import_module("." + _m, __name__)

_utils = importlib.import_module(".00_utils", __name__)
_fdata = importlib.import_module(".01_features_data", __name__)
_wdata = importlib.import_module(".02_weekly_data", __name__)
_clust = importlib.import_module(".03_clustering", __name__)
_stab = importlib.import_module(".04_stability", __name__)
_regr = importlib.import_module(".06_regression", __name__)
_pred = importlib.import_module(".07_prediction", __name__)
_art = importlib.import_module(".08_artifacts", __name__)

PROJECT_ROOT = _utils.PROJECT_ROOT
load_config = _utils.load_config
get_features_csv = _utils.get_features_csv
get_variable_desc_csv = _utils.get_variable_desc_csv
get_weekly_parquet = _utils.get_weekly_parquet
get_meta_csv = _utils.get_meta_csv
get_output_dir = _utils.get_output_dir
load_features = _fdata.load_features
load_variable_description = _fdata.load_variable_description
load_weekly = _wdata.load_weekly
load_meta = _wdata.load_meta
fit_kmeans = _clust.fit_kmeans
cluster_stability_score = _stab.cluster_stability_score
prepare_design_matrix = _regr.prepare_design_matrix
ols_fit = _regr.ols_fit
predict_ols = _pred.predict_ols
mse = _pred.mse
save_table = _art.save_table
save_figure = _art.save_figure
save_model = _art.save_model
load_model = _art.load_model

__all__ = [
    "PROJECT_ROOT",
    "load_config",
    "get_features_csv",
    "get_variable_desc_csv",
    "get_weekly_parquet",
    "get_meta_csv",
    "get_output_dir",
    "load_features",
    "load_variable_description",
    "load_weekly",
    "load_meta",
    "fit_kmeans",
    "cluster_stability_score",
    "prepare_design_matrix",
    "ols_fit",
    "predict_ols",
    "mse",
    "save_table",
    "save_figure",
    "save_model",
    "load_model",
]

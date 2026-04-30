# 260303 Reproducibility Guide

## Environment
1. Create/activate virtual environment.
2. Install dependencies from project requirements.

## Baseline pipeline
```bash
.venv/bin/python 260303/run_all.py
```

## Robustness pipeline
```bash
.venv/bin/python 260303/03_robustness/run_01_label_robustness.py
.venv/bin/python 260303/03_robustness/run_02_sample_robustness.py
.venv/bin/python 260303/03_robustness/run_03_model_robustness.py
.venv/bin/python 260303/03_robustness/run_04_build_master_table.py
```

## Practical impact pipeline
```bash
.venv/bin/python 260303/04_practical_impact/run_practical_impact_metrics.py
```

## Thesis docs templates
```bash
.venv/bin/python 260303/05_thesis_docs/generate_doc_templates.py
.venv/bin/python 260303/05_thesis_docs/generate_result_inventory.py
```

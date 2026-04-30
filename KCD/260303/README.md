# 260303 — Life cycle classification experiment

## Label scheme

- **final_code** = Period1 + Period2 + Pattern (e.g. `UUZ`, `DDY`, `DUX`).
- **Period 1 / Period 2**: `U` = rising, `D` = falling.
- **Pattern** (over entire period): `X` = rising, `Y` = stable, `Z` = declining.

## Y variable: life_cycle_category

| Pattern | life_cycle_category |
|--------|----------------------|
| X      | **rising**           |
| Y      | **maintaining**      |
| Z      | **declining**        |

## Pipeline

1. **01_merge_labels**: Merge base features + final_code → `life_cycle_category`.
2. **02_regression**: Summary by category + Multinomial Logit (baseline = maintaining).

## Run

From project root (26-1):

```bash
.venv/bin/python 260303/run_all.py
```

## Outputs

- `outputs/tables/df_for_life_cycle_regression.csv` — merged data with `life_cycle_category`
- `outputs/tables/life_cycle_summary_key_vars.csv` — summary stats by category
- `outputs/tables/multinomial_logit_life_cycle_coefficients.csv` — MNL coefficients
- `outputs/tables/multinomial_logit_life_cycle_summary.txt` — full model summary

---

## Thesis-prep extension (robustness + practical impact + docs)

Run sequentially from project root (`26-1`):

```bash
.venv/bin/python 260303/run_thesis_prep.py
```

Dry-run (command list only):

```bash
.venv/bin/python 260303/run_thesis_prep.py --dry-run
```

Main added scripts:
- `260303/03_robustness/run_01_label_robustness.py`
- `260303/03_robustness/run_02_sample_robustness.py`
- `260303/03_robustness/run_03_model_robustness.py`
- `260303/03_robustness/run_04_build_master_table.py`
- `260303/04_practical_impact/run_practical_impact_metrics.py`
- `260303/05_thesis_docs/generate_doc_templates.py`
- `260303/05_thesis_docs/generate_result_inventory.py`

Expected new outputs:
- `260303/outputs/tables/robustness_label_results.csv`
- `260303/outputs/tables/robustness_sample_results.csv`
- `260303/outputs/tables/robustness_model_results.csv`
- `260303/outputs/tables/robustness_master_table.csv`
- `260303/outputs/tables/practical_impact_metrics.csv`
- `260303/docs/*.md`

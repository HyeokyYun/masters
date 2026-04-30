"""Generate thesis-ready markdown templates for 260303."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "260303" / "docs"

TEMPLATES = {
    "thesis_claims_v1.md": """# Thesis Claims v1

## Claim 1
- Statement:
- Why this matters:
- Evidence files:

## Claim 2
- Statement:
- Why this matters:
- Evidence files:

## Claim 3
- Statement:
- Why this matters:
- Evidence files:

## Mapping: Claim -> Table/Figure
| Claim | Table | Figure | Robustness support |
|---|---|---|---|
| Claim 1 |  |  |  |
| Claim 2 |  |  |  |
| Claim 3 |  |  |  |
""",
    "result_inventory_v1.md": """# Result Inventory v1

## Core tables
- 260303/outputs/tables/df_for_life_cycle_regression.csv
- 260303/outputs/tables/life_cycle_summary_key_vars.csv
- 260303/outputs/tables/multinomial_logit_life_cycle_coefficients.csv

## Robustness tables
- 260303/outputs/tables/robustness_label_results.csv
- 260303/outputs/tables/robustness_sample_results.csv
- 260303/outputs/tables/robustness_model_results.csv
- 260303/outputs/tables/robustness_master_table.csv

## Practical impact table
- 260303/outputs/tables/practical_impact_metrics.csv

## Pending figure/table generation
- [ ]
""",
    "limitations_and_identification.md": """# Limitations and Identification

## Interpretation boundary
- This thesis reports associations, not strict causal effects.

## Main threats
1. Omitted variables:
2. Endogeneity:
3. Sample selection:
4. Measurement error:

## Mitigation used
- Control variables:
- Fixed effects / subgroup checks:
- Robustness checks:

## Remaining risk
- What may still bias estimates:

## Future identification strategy
- Natural experiment / IV / panel design proposals:
""",
    "chapter_results_v1.md": """# Chapter: Results (Draft v1)

## 1. Baseline findings
- Key pattern:
- Main table references:

## 2. Robustness findings
- Label robustness summary:
- Sample robustness summary:
- Model robustness summary:

## 3. Practical impact
- Early-risk targeting performance:
- Intervention lead-time interpretation:

## 4. Short takeaways
1.
2.
3.
""",
    "chapter_discussion_v1.md": """# Chapter: Discussion (Draft v1)

## Policy implications
1.
2.
3.

## Business implications
1.
2.

## Boundary of external validity
- Where this result is likely to hold:
- Where caution is needed:

## Research contribution summary
- Method contribution:
- Empirical contribution:
""",
    "appendix_tables_figures_v1.md": """# Appendix: Tables and Figures (Draft v1)

## A. Variable definitions
- File: basic_data/variable_description.csv

## B. Additional regression tables
- robustness_master_table.csv

## C. Additional prediction diagnostics
- practical_impact_metrics.csv

## D. Reproducibility notes
- Execution commands:
- Environment:
""",
    "pre_submission_checklist.md": """# Pre-submission Checklist

## Consistency
- [ ] Research question and conclusion align
- [ ] Claim-to-evidence mapping complete
- [ ] Table/figure numbering is consistent

## Statistical reporting
- [ ] Baseline model specification described
- [ ] Robustness results summarized in one master table
- [ ] Limitations clearly stated

## Reproducibility
- [ ] One-command pipeline documented
- [ ] Input/output paths fixed
- [ ] Environment and dependencies listed

## Final QA
- [ ] Typos and notation check
- [ ] References and appendices linked
""",
}

README_REPRO = """# 260303 Reproducibility Guide

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
"""


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    for filename, body in TEMPLATES.items():
        path = DOCS / filename
        if not path.exists():
            path.write_text(body, encoding="utf-8")

    repro_path = ROOT / "260303" / "README_repro.md"
    if not repro_path.exists():
        repro_path.write_text(README_REPRO, encoding="utf-8")


if __name__ == "__main__":
    main()

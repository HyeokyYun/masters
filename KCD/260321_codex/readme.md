# 260321_codex

`260321_codex` is a follow-up analysis package created from the 2026-03-19 meeting notes.

It is designed to answer the concrete next-step questions raised in the meeting:

1. redefine sales volatility around trend instead of around the mean,
2. test category-by-competition interactions,
3. re-check business age and young-store subsamples,
4. add owner demographics where available,
5. organize the forecasting benchmark task.

## Structure

```text
260321_codex/
├── main.py
├── readme.md
├── src/
│   ├── config.py
│   ├── step01_build_base_dataset.py
│   ├── step02_volatility_analysis.py
│   ├── step03_followup_analysis.py
│   └── step04_reporting.py
└── outputs/
    ├── docs/
    ├── figures/
    └── tables/
```

## Run

```bash
cd 260321_codex
../.venv/bin/python main.py
```

Run a single step:

```bash
../.venv/bin/python main.py --step 2
```

## Main outputs

- `outputs/tables/meeting_base_dataset.csv`
- `outputs/tables/volatility_candidate_metrics.csv`
- `outputs/tables/volatility_metric_screening.csv`
- `outputs/tables/business_age_bucket_summary.csv`
- `outputs/tables/industry_competition_summary.csv`
- `outputs/tables/mnlogit_outcome3_base_coefficients.csv`
- `outputs/tables/mnlogit_outcome3_interaction_coefficients.csv`
- `outputs/tables/forecasting_benchmark_template.csv`
- `outputs/docs/meeting_action_plan.md`

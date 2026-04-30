# 260321 Meeting Action Plan

## What was requested in the meeting

1. Redefine sales volatility so that it measures deviation around a growth trend rather than deviation around a flat mean.
2. Test competition or crowding interactions, especially for fast-food stores.
3. Re-check business age and run a separate analysis for young stores.
4. Add owner demographics when available.
5. Benchmark forecasting performance against literature.
6. Treat franchise status cautiously because missingness is high.

## What this folder now does

1. Builds an enriched base dataset by merging the current labeled lifecycle output with `meta.csv` and weekly observation bounds.
2. Computes multiple candidate volatility metrics:
   - `vol_cv_mean`
   - `vol_resid_linear`
   - `vol_resid_quadratic`
   - `vol_resid_rolling13`
   - `vol_resid_stl13`
3. Creates dong-level competition metrics and interaction-ready variables.
4. Summarizes business-age buckets and runs an early-store subsample model.
5. Merges owner age, checks whether owner gender exists, and records missingness.
6. Writes a forecasting benchmark template for the external literature review.

## Immediate interpretation

- Recommended volatility candidate for the next meeting: `vol_resid_rolling13`
- Sample size in the new base table: `21,365`
- Missing owner-age rate: `0.075`
- Missing owner-gender rate: `1.000`
- Young-store observations in 0-12 months buckets: `670`

## Recommended next actions

1. Review `volatility_metric_screening.csv` and choose one trend-relative volatility definition for the main table.
2. Check `mnlogit_outcome3_interaction_*` outputs to see whether fast-food crowding changes the growth/stable/decline odds.
3. Use `business_age_bucket_summary.csv` and the young-store model to define the final cutoff for "short business age".
4. If owner gender exists in another source, merge it into `meeting_base_dataset.csv` and rerun this folder.
5. Fill the external forecasting benchmark template with literature values before claiming whether 0.37 to 0.43 is high.
6. Keep franchise status out of the main model unless a defensible missing-data rule is agreed upon.

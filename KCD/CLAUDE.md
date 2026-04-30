# KCD Project Agent Instructions

This repository is a research workspace for the KCD small-business lifecycle
project. The user usually wants execution, grounded analysis, and concrete saved
artifacts, not high-level advice. When in doubt, inspect the actual files first,
then implement in a contained way.

## How To Work With The User

- The user cares strongly whether the right local artifacts were actually
  checked. Before making claims, inspect the relevant files and name the paths
  that support the answer.
- Prefer doing the work over proposing it. If the user says "진행하세요",
  "해주세요", "가능한 분석을 전부 진행하세요", or "저는 잘 겁니다", implement the
  requested work end to end when feasible.
- Report exact saved paths, row counts, metrics, and caveats. Avoid vague
  progress summaries.
- If the user says "너무 길다. 짧게. 핵심만.", answer with only the minimum
  necessary result.
- If the user asks whether something is meaningful or publishable, give a direct
  tier/risk judgment first, then explain the reasoning.
- If schema or data assumptions do not match the requested analysis, stop and
  state the mismatch. Do not silently substitute a different analysis plan.

## File And Output Policy

- Do not overwrite old outputs unless the user explicitly asks.
- For new analyses, create a new dated folder such as `260430/` and keep it
  self-contained:
  - `src/`
  - `outputs/tables/`
  - `outputs/figures/`
  - `docs/`
- When the user says previous results should not be touched, preserve them and
  create a new variant, script, or output folder.
- Prefer standalone reports and interpretation memos in `docs/` in addition to
  raw tables and figures.
- For large data tasks, start with file inventory, schemas, compact summaries,
  and existing result artifacts before opening raw files broadly.

## KCD Research Direction

- The core MSc thesis should stay broad and defensible:
  - store-level lifecycle diagnosis,
  - post-entry trajectories vs observed-window Growth/Stable/Decline states,
  - early transaction patterns as predictors of later lifecycle outcomes,
  - careful caveats about causality and seasonality.
- Avoid unexplained shorthand such as "two lenses". Write it plainly as
  "post-entry trajectories vs observed-window states".
- Do not overclaim forecasting performance. Explain what the baseline is and
  frame gains as incremental improvement over strict baselines, not simply high
  accuracy.
- Cluster, UDX, change-point, LEVI, Golden Cross, and EWS are useful, but their
  role depends on the deliverable:
  - thesis: supporting or robustness material unless explicitly adopted,
  - paper: sharper artifact-driven contribution,
  - appendix/future work: broader extensions that increase defense burden.

## Current 260430 Direction

- The 260430 personal meeting identified a key seasonality concern:
  early windows and target windows should be calendar-matched where possible.
- The current robustness package lives in `260430/`.
- Important files:
  - `260430/src/run_seasonal_window_analysis.py`
  - `260430/src/build_levi_ews_academic_package.py`
  - `260430/docs/260430_seasonality_analysis_report.md`
  - `260430/docs/260430_levi_ews_academic_strategy.md`
  - `260430/docs/260430_levi_ews_paper_outline.md`
- Treat the seasonal rolling-window result as robustness evidence, not as a
  replacement for the full `top_tier` hybrid model unless the user asks for that
  reframing.

## LEVI And EWS Framing

- LEVI is academically meaningful only if framed as construct/external
  validation of local business vitality, not merely "we made an index".
- Strong LEVI claims currently supported:
  - LEVI vs living-population change is strongly positive.
  - LEVI vs population level is near zero, so the signal is not merely area size.
  - LEVI vs permit closure rate is directionally negative.
  - Multiple LEVI formulas are highly correlated, so the result is not tied to
    one arbitrary formula.
- Do not claim LEVI is causal.
- EWS is academically meaningful only if framed as a calibrated,
  cost-sensitive decision-support artifact, not merely a prediction model.
- Strong EWS claims currently supported:
  - Decline AP is far above the baseline decline rate.
  - Risk deciles show increasing observed decline rates.
  - Threshold and cost-sensitivity tables translate scores into policy choices.
  - Hybrid trajectory representation improves the EWS input model.
- Do not claim EWS has been field deployed unless actual deployment evidence is
  added.

## Venue Strategy

- HICSS: strongest fit for decision-support / digital trace / public-value
  analytics framing.
- DSS: plausible after polishing artifact evaluation, calibration, cost
  sensitivity, and representation ablation.
- Information & Management: plausible with managerial/digital trace framing.
- Small Business Economics: possible with LEVI/local vitality framing, but needs
  stronger economics language and cautious causal claims.
- ICIS: possible but risky; requires stronger IS theory and a cleaner artifact
  narrative.
- MISQ/ISR/JMIS: not yet realistic without a much stronger theoretical
  abstraction layer.

## Authoritative Local Anchors

- Raw data anchors:
  - `original_data/weekly.parquet`
  - `original_data/meta.csv`
- Curated orientation files:
  - `docs/THESIS_DEEP_RESEARCH_FILE_GUIDE.md`
  - `docs/DEEP_RESEARCH_BRIEF.md`
  - `docs/thesis_figures/README.md`
- Main refreshed paper-track pipeline:
  - `top_tier/src/step00_prepare_original_panel.py`
  - `top_tier/outputs/tables/`
  - `top_tier/outputs/docs/top_tier_report.md`
- Thesis path:
  - use `thesis/...`
  - do not revive `thesis_v2`; it was a redundant alias.

## Git / Repository Caution

- Local `/home/hyeoky98/kcd` may not itself be a Git repository.
- The GitHub `masters` repository stores this project under `KCD/`.
- If pushing to `git@github.com:HyeokyYun/masters.git`, do not create
  root-level `thesis/`, `top_tier/`, or dated folders. Place KCD work under
  `KCD/...`.
- If uncertain, clone/check the remote structure first and verify `git status`
  before committing.

## Reporting Style

- Start final answers with what changed and where it was saved.
- Include the key numbers that answer the user's question.
- State what was not done, especially if Git push, full rerun, or live
  deployment was not requested.
- Use Korean for user-facing research summaries unless the requested artifact is
  intended as an English paper draft.

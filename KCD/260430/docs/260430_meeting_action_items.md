# 260430 Personal Meeting Action Items

Source: `thesis/meeting_stt/260430_personal_meeting.txt`

## Main Technical Issue

The current prediction setup uses an early observation window to predict a late
window near the end of the data. Because the data run from 2021-01 to 2023-08,
the late window can fall in a different season from the early window. This can
confound lifecycle signal with calendar seasonality.

The requested correction is to compare like with like:

- January-March early windows should be compared with January-March target windows.
- February-April windows should be compared with February-April target windows.
- The same logic should be repeated over multiple start months and window lengths.

## New Analysis To Run

1. Build calendar-matched rolling windows from `original_data/weekly.parquet`.
2. For each start month and window length, compare a feature window with the same
   calendar window one or two years later when available.
3. Re-label Growth, Stable, and Decline from the target-window slope.
4. Re-run predictive evaluation using only feature-window information.
5. Compare seasonal-window results against the existing `top_tier` baseline.

## Thesis Positioning

The thesis should stay focused on the store-level lifecycle and prediction story.

LEVI, city-level vitality, Golden Cross, and EWS are useful supporting ideas, but
the meeting conclusion was that they should not become the main MSc thesis story
unless additional theory or technical novelty is added.

Recommended positioning:

- Main thesis: store-level early trajectory and later Growth/Stable/Decline.
- Supporting evidence: Golden Cross and public-data validation.
- Future work / journal extension: LEVI and city-level economic vitality.
- Application angle: EWS as policy or financial screening support.

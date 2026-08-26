:param_1 -- ============================================================
-- Outlet Channel Change Summary by Transition Pattern
-- Purpose: Summarize outlet channel changes by old-to-new channel
--   transition pattern, showing how many outlets moved between each
--   channel pair and the date range of changes.
-- Source: aistra_ayush.gold.kpi_008_channel_changes
-- Parameters: start_date, end_date
-- ============================================================

SELECT
  dimension_old_channel AS from_channel,
  dimension_new_channel AS to_channel,
  COUNT(*) AS outlet_change_count,
  COUNT(DISTINCT dimension_outlet) AS unique_outlets_changed,
  MIN(period_start) AS earliest_change_date,
  MAX(period_start) AS latest_change_date
FROM aistra_ayush.gold.kpi_008_channel_changes
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
GROUP BY dimension_old_channel, dimension_new_channel
ORDER BY outlet_change_count DESC;
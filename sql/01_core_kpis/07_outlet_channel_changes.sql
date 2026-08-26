-- ============================================================
-- KPI-008: Outlet Channel Change Count
-- Business Definition: Count of outlets whose channel classification
--   changed during the selected period, based on effective-dated
--   outlet master history (SCD Type 2). Multiple changes within a
--   period are counted as separate changes.
-- Grain: change_event (one row per outlet per change)
-- Metric: metric_value = 1 per change event
-- Unit: COUNT
-- Source: aistra_ayush.gold.kpi_008_channel_changes
-- Filters: Excludes first record (no prior state); only counts
--   actual channel changes (previous_channel != channel).
-- Parameters: start_date, end_date, outlet
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS change_date,
  period_end,
  grain,
  dimension_outlet AS outlet_code,
  dimension_old_channel AS old_channel,
  dimension_new_channel AS new_channel,
  metric_value AS change_count,
  metric_unit,
  calculated_at
FROM aistra_ayush.gold.kpi_008_channel_changes
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:outlet = 'ALL' OR dimension_outlet = :outlet)
ORDER BY change_date, outlet_code;
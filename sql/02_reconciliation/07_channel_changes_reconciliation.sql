-- ============================================================
-- Reconciliation: KPI-008 Channel Changes vs Silver Outlets SCD2
-- Purpose: Verify that Gold KPI-008 channel change count matches
--   an independently calculated count from the Silver outlets table
--   using the same SCD Type 2 logic (LAG-based channel change detection).
--   Also validates that no changes have NULL old/new channels.
-- Gold Source: aistra_ayush.gold.kpi_008_channel_changes
-- Silver Source: aistra_ayush.silver.outlets
-- Pass condition: counts match and no NULL channels
-- ============================================================

WITH silver_changes AS (
  SELECT
    outlet_code,
    effective_from AS change_date,
    LAG(channel) OVER (PARTITION BY outlet_code ORDER BY effective_from) AS previous_channel,
    channel AS new_channel
  FROM aistra_ayush.silver.outlets
  WHERE effective_from IS NOT NULL
),
silver_actual_changes AS (
  SELECT *
  FROM silver_changes
  WHERE previous_channel IS NOT NULL
    AND previous_channel != new_channel
)
SELECT
  'KPI-008 vs Silver' AS reconciliation_check,
  (SELECT COUNT(*) FROM aistra_ayush.gold.kpi_008_channel_changes) AS kpi_008_change_count,
  (SELECT COUNT(*) FROM silver_actual_changes) AS silver_change_count,
  (SELECT COUNT(*) FROM aistra_ayush.gold.kpi_008_channel_changes)
  - (SELECT COUNT(*) FROM silver_actual_changes) AS difference,
  (SELECT COUNT(*) FROM aistra_ayush.gold.kpi_008_channel_changes
   WHERE dimension_old_channel IS NULL OR dimension_new_channel IS NULL) AS null_channels_in_gold,
  CASE
    WHEN (SELECT COUNT(*) FROM aistra_ayush.gold.kpi_008_channel_changes)
       = (SELECT COUNT(*) FROM silver_actual_changes)
    AND (SELECT COUNT(*) FROM aistra_ayush.gold.kpi_008_channel_changes
         WHERE dimension_old_channel IS NULL OR dimension_new_channel IS NULL) = 0
    THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
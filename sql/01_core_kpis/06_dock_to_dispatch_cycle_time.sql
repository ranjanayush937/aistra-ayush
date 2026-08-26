-- ============================================================
-- KPI-007: Median Dock-to-Dispatch Cycle Time (Monthly by Warehouse)
-- Business Definition: Median elapsed time in hours between warehouse
--   RECEIVE and DISPATCH events for completed warehouse movements.
--   Requires both events; excludes negative durations.
-- Grain: month, warehouse_code
-- Metric: metric_value = PERCENTILE_CONT(0.5) of cycle_hours
-- Unit: HOURS
-- Source: aistra_ayush.gold.kpi_007_cycle_time
-- Filters: Both RECEIVE and DISPATCH events must exist;
--   dispatch_time > dock_time (no negative durations)
-- Parameters: start_date, end_date, warehouse
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  dimension_warehouse AS warehouse_code,
  ROUND(metric_value, 2) AS median_cycle_hours,
  metric_unit,
  source_row_count AS completed_movements,
  min_cycle_hours,
  max_cycle_hours,
  calculated_at
FROM aistra_ayush.gold.kpi_007_cycle_time
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:warehouse = 'ALL' OR dimension_warehouse = :warehouse)
ORDER BY month_start, warehouse_code;
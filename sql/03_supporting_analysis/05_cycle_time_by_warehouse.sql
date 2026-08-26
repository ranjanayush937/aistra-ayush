-- ============================================================
-- Cycle Time Performance by Warehouse (Monthly Summary)
-- Purpose: Compare median dock-to-dispatch cycle times across
--   warehouses, with month-over-month trend for the worst-performing
--   and best-performing facilities.
-- Source: aistra_ayush.gold.kpi_007_cycle_time
-- Parameters: start_date, end_date, warehouse
-- ============================================================

SELECT
  period_start AS month_start,
  dimension_warehouse AS warehouse_code,
  ROUND(metric_value, 2) AS median_cycle_hours,
  source_row_count AS completed_movements,
  min_cycle_hours,
  max_cycle_hours,
  LAG(ROUND(metric_value, 2)) OVER (
    PARTITION BY dimension_warehouse ORDER BY period_start
  ) AS prev_month_median_hours,
  ROUND(
    metric_value - LAG(metric_value) OVER (
      PARTITION BY dimension_warehouse ORDER BY period_start
    ),
    2
  ) AS mom_change_hours
FROM aistra_ayush.gold.kpi_007_cycle_time
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:warehouse = 'ALL' OR dimension_warehouse = :warehouse)
ORDER BY month_start, median_cycle_hours DESC;
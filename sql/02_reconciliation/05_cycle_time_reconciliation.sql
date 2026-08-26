-- ============================================================
-- Reconciliation: KPI-007 Cycle Time vs Silver WMS Events
-- Purpose: Verify that the count of completed warehouse movements
--   in Gold KPI-007 matches the independently calculated count from
--   Silver wms_events (orders with both RECEIVE and DISPATCH, excluding
--   negative durations). Also validates that all cycle times are positive.
-- Gold Source: aistra_ayush.gold.kpi_007_cycle_time
-- Silver Source: aistra_ayush.silver.wms_events
-- Pass condition: movement counts match and min metric_value >= 0
-- ============================================================

-- Part 1: Total completed movements comparison
SELECT
  'KPI-007 movements vs Silver' AS reconciliation_check,
  (SELECT SUM(source_row_count)
   FROM aistra_ayush.gold.kpi_007_cycle_time) AS kpi_007_total_movements,
  (
    SELECT COUNT(*)
    FROM (
      SELECT order_number, warehouse_code,
             MIN(CASE WHEN event_type = 'RECEIVE' THEN event_timestamp END) AS dock_time,
             MAX(CASE WHEN event_type = 'DISPATCH' THEN event_timestamp END) AS dispatch_time
      FROM aistra_ayush.silver.wms_events
      GROUP BY order_number, warehouse_code
      HAVING dock_time IS NOT NULL AND dispatch_time IS NOT NULL
    ) ep
    WHERE ep.dispatch_time > ep.dock_time
  ) AS silver_completed_movements,
  CASE
    WHEN (
      (SELECT SUM(source_row_count) FROM aistra_ayush.gold.kpi_007_cycle_time)
      = (
        SELECT COUNT(*)
        FROM (
          SELECT order_number, warehouse_code,
                 MIN(CASE WHEN event_type = 'RECEIVE' THEN event_timestamp END) AS dock_time,
                 MAX(CASE WHEN event_type = 'DISPATCH' THEN event_timestamp END) AS dispatch_time
          FROM aistra_ayush.silver.wms_events
          GROUP BY order_number, warehouse_code
          HAVING dock_time IS NOT NULL AND dispatch_time IS NOT NULL
        ) ep
        WHERE ep.dispatch_time > ep.dock_time
      )
    ) THEN 'PASS'
    ELSE 'FAIL'
  END AS status

UNION ALL

-- Part 2: Validate no negative cycle times exist in Gold
SELECT
  'KPI-007 positive cycle times' AS reconciliation_check,
  COUNT(*) AS kpi_007_total_warehouse_months,
  0 AS silver_completed_movements,
  CASE
    WHEN MIN(metric_value) >= 0 THEN 'PASS'
    ELSE 'FAIL - Negative cycle times found'
  END AS status
FROM aistra_ayush.gold.kpi_007_cycle_time;
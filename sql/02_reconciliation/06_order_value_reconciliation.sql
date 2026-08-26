-- ============================================================
-- Reconciliation: KPI-009 Order Value vs Silver Sales Orders
-- Purpose: Verify that Gold KPI-009 total order value matches an
--   independently calculated sum from the Silver sales_orders table.
--   Also checks order count reconciliation.
-- Gold Source: aistra_ayush.gold.kpi_009_order_value_by_system
-- Silver Source: aistra_ayush.silver.sales_orders
-- Pass condition: value difference < 0.01 USD and count matches
-- ============================================================

SELECT
  'KPI-009 value vs Silver' AS reconciliation_check,
  (SELECT ROUND(SUM(metric_value), 2)
   FROM aistra_ayush.gold.kpi_009_order_value_by_system) AS kpi_009_total_value_usd,
  (SELECT ROUND(SUM(order_value_gross), 2)
   FROM aistra_ayush.silver.sales_orders
   WHERE order_value_gross IS NOT NULL) AS silver_total_value_usd,
  ROUND(
    (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_009_order_value_by_system)
    - (SELECT SUM(order_value_gross) FROM aistra_ayush.silver.sales_orders
       WHERE order_value_gross IS NOT NULL),
    2
  ) AS value_difference_usd,
  (SELECT SUM(source_row_count) FROM aistra_ayush.gold.kpi_009_order_value_by_system) AS kpi_order_count,
  (SELECT COUNT(*) FROM aistra_ayush.silver.sales_orders
   WHERE order_value_gross IS NOT NULL) AS silver_order_count,
  CASE
    WHEN ABS(
      (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_009_order_value_by_system)
      - (SELECT SUM(order_value_gross) FROM aistra_ayush.silver.sales_orders
         WHERE order_value_gross IS NOT NULL)
    ) < 0.01
    AND (
      (SELECT SUM(source_row_count) FROM aistra_ayush.gold.kpi_009_order_value_by_system)
      = (SELECT COUNT(*) FROM aistra_ayush.silver.sales_orders WHERE order_value_gross IS NOT NULL)
    ) THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
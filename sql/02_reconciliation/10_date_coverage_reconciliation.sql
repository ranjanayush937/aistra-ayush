-- ============================================================
-- Date Coverage Reconciliation: Gold vs Silver Date Ranges
-- Purpose: Verify that Gold KPI tables cover the same date range
--   as their underlying Silver source tables. Gaps would indicate
--   missing data in the Gold pipeline or filtering issues.
-- Pass condition: Gold and Silver min/max dates match
-- ============================================================

SELECT
  'KPI-001 date range' AS check_name,
  (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_001_gross_sales) AS gold_min_date,
  (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_001_gross_sales) AS gold_max_date,
  (SELECT MIN(business_date) FROM aistra_ayush.silver.transactions) AS silver_min_date,
  (SELECT MAX(business_date) FROM aistra_ayush.silver.transactions) AS silver_max_date,
  CASE
    WHEN (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_001_gross_sales)
       = (SELECT MIN(business_date) FROM aistra_ayush.silver.transactions)
    AND (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_001_gross_sales)
       = (SELECT MAX(business_date) FROM aistra_ayush.silver.transactions)
    THEN 'PASS' ELSE 'CHECK'
  END AS status

UNION ALL

SELECT
  'KPI-005 date range' AS check_name,
  (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate) AS gold_min_date,
  (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate) AS gold_max_date,
  (SELECT DATE_TRUNC('month', MIN(reading_date)) FROM aistra_ayush.silver.reefer_telemetry) AS silver_min_date,
  (SELECT DATE_TRUNC('month', MAX(reading_date)) FROM aistra_ayush.silver.reefer_telemetry) AS silver_max_date,
  CASE
    WHEN (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate)
       = (SELECT DATE_TRUNC('month', MIN(reading_date)) FROM aistra_ayush.silver.reefer_telemetry)
    AND (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate)
       = (SELECT DATE_TRUNC('month', MAX(reading_date)) FROM aistra_ayush.silver.reefer_telemetry)
    THEN 'PASS' ELSE 'CHECK'
  END AS status

UNION ALL

SELECT
  'KPI-007 date range' AS check_name,
  (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_007_cycle_time) AS gold_min_date,
  (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_007_cycle_time) AS gold_max_date,
  (SELECT DATE_TRUNC('month', MIN(event_date)) FROM aistra_ayush.silver.wms_events) AS silver_min_date,
  (SELECT DATE_TRUNC('month', MAX(event_date)) FROM aistra_ayush.silver.wms_events) AS silver_max_date,
  CASE
    WHEN (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_007_cycle_time)
       = (SELECT DATE_TRUNC('month', MIN(event_date)) FROM aistra_ayush.silver.wms_events)
    AND (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_007_cycle_time)
       = (SELECT DATE_TRUNC('month', MAX(event_date)) FROM aistra_ayush.silver.wms_events)
    THEN 'PASS' ELSE 'CHECK'
  END AS status

UNION ALL

SELECT
  'KPI-009 date range' AS check_name,
  (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_009_order_value_by_system) AS gold_min_date,
  (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_009_order_value_by_system) AS gold_max_date,
  (SELECT DATE_TRUNC('month', MIN(order_date)) FROM aistra_ayush.silver.sales_orders) AS silver_min_date,
  (SELECT DATE_TRUNC('month', MAX(order_date)) FROM aistra_ayush.silver.sales_orders) AS silver_max_date,
  CASE
    WHEN (SELECT MIN(period_start) FROM aistra_ayush.gold.kpi_009_order_value_by_system)
       = (SELECT DATE_TRUNC('month', MIN(order_date)) FROM aistra_ayush.silver.sales_orders)
    AND (SELECT MAX(period_start) FROM aistra_ayush.gold.kpi_009_order_value_by_system)
       = (SELECT DATE_TRUNC('month', MAX(order_date)) FROM aistra_ayush.silver.sales_orders)
    THEN 'PASS' ELSE 'CHECK'
  END AS status;
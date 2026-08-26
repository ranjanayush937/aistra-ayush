-- ============================================================
-- Duplicate Key Checks Across Gold KPI Tables
-- Purpose: Verify that each Gold KPI table has no duplicate rows
--   at its declared grain. A duplicate would indicate an aggregation
--   or grouping issue in the Gold pipeline.
-- Pass condition: all duplicate counts = 0
-- ============================================================

-- KPI-001: Should have one row per business_date
SELECT 'KPI-001 duplicate dates' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT period_start) AS unique_dates,
  COUNT(*) - COUNT(DISTINCT period_start) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT period_start) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_001_gross_sales

UNION ALL

-- KPI-002: Should have one row per business_date + channel
SELECT 'KPI-002 duplicate date+channel' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(period_start, '|', dimension_channel)) AS unique_keys,
  COUNT(*) - COUNT(DISTINCT CONCAT(period_start, '|', dimension_channel)) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT CONCAT(period_start, '|', dimension_channel)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_002_sales_by_channel

UNION ALL

-- KPI-003: Should have one row per business_date + sku_code
SELECT 'KPI-003 duplicate date+sku' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(period_start, '|', dimension_sku)) AS unique_keys,
  COUNT(*) - COUNT(DISTINCT CONCAT(period_start, '|', dimension_sku)) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT CONCAT(period_start, '|', dimension_sku)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_003_units_sold_eaches

UNION ALL

-- KPI-005: Should have one row per month
SELECT 'KPI-005 duplicate months' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT period_start) AS unique_months,
  COUNT(*) - COUNT(DISTINCT period_start) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT period_start) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_005_temp_excursion_rate

UNION ALL

-- KPI-006: Should have one row per month + vendor
SELECT 'KPI-006 duplicate month+vendor' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(period_start, '|', dimension_vendor)) AS unique_keys,
  COUNT(*) - COUNT(DISTINCT CONCAT(period_start, '|', dimension_vendor)) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT CONCAT(period_start, '|', dimension_vendor)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_006_temp_excursion_by_carrier

UNION ALL

-- KPI-007: Should have one row per month + warehouse
SELECT 'KPI-007 duplicate month+warehouse' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(period_start, '|', dimension_warehouse)) AS unique_keys,
  COUNT(*) - COUNT(DISTINCT CONCAT(period_start, '|', dimension_warehouse)) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT CONCAT(period_start, '|', dimension_warehouse)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_007_cycle_time

UNION ALL

-- KPI-009: Should have one row per month + source_system
SELECT 'KPI-009 duplicate month+system' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT CONCAT(period_start, '|', dimension_source_system)) AS unique_keys,
  COUNT(*) - COUNT(DISTINCT CONCAT(period_start, '|', dimension_source_system)) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT CONCAT(period_start, '|', dimension_source_system)) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_009_order_value_by_system

UNION ALL

-- KPI-012: Should have one row per month
SELECT 'KPI-012 duplicate months' AS check_name,
  COUNT(*) AS total_rows,
  COUNT(DISTINCT period_start) AS unique_months,
  COUNT(*) - COUNT(DISTINCT period_start) AS duplicates,
  CASE WHEN COUNT(*) = COUNT(DISTINCT period_start) THEN 'PASS' ELSE 'FAIL' END AS status
FROM aistra_ayush.gold.kpi_012_order_pos_reconciliation;
-- ============================================================
-- Reconciliation: KPI-002 Channel Sum vs KPI-001 Total
-- Purpose: Verify that the sum of KPI-002 channel-level sales
--   equals the KPI-001 daily total. A mismatch would indicate
--   that the SCD Type 2 channel join caused row loss or duplication.
-- Gold Sources:
--   aistra_ayush.gold.kpi_002_sales_by_channel
--   aistra_ayush.gold.kpi_001_gross_sales
-- Pass condition: difference < 0.01 USD
-- ============================================================

SELECT
  'KPI-002 channel sum vs KPI-001' AS reconciliation_check,
  (SELECT ROUND(SUM(metric_value), 2)
   FROM aistra_ayush.gold.kpi_002_sales_by_channel) AS kpi_002_total_usd,
  (SELECT ROUND(SUM(metric_value), 2)
   FROM aistra_ayush.gold.kpi_001_gross_sales) AS kpi_001_total_usd,
  ROUND(
    (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_002_sales_by_channel)
    - (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_001_gross_sales),
    2
  ) AS difference_usd,
  CASE
    WHEN ABS(
      (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_002_sales_by_channel)
      - (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_001_gross_sales)
    ) < 0.01 THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
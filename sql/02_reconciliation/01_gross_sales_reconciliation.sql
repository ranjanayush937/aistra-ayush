-- ============================================================
-- Reconciliation: KPI-001 Gross Sales vs Silver Transactions Total
-- Purpose: Verify that Gold KPI-001 total matches an independently
--   calculated sum from the Silver transactions table.
-- Gold Source: aistra_ayush.gold.kpi_001_gross_sales
-- Silver Source: aistra_ayush.silver.transactions
-- Pass condition: difference < 0.01 USD
-- ============================================================

SELECT
  'KPI-001 vs Silver' AS reconciliation_check,
  (SELECT ROUND(SUM(metric_value), 2)
   FROM aistra_ayush.gold.kpi_001_gross_sales) AS kpi_001_total_usd,
  (SELECT ROUND(SUM(line_sales_value_pretax), 2)
   FROM aistra_ayush.silver.transactions
   WHERE line_sales_value_pretax IS NOT NULL) AS silver_total_usd,
  ROUND(
    (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_001_gross_sales)
    - (SELECT SUM(line_sales_value_pretax) FROM aistra_ayush.silver.transactions
       WHERE line_sales_value_pretax IS NOT NULL),
    2
  ) AS difference_usd,
  CASE
    WHEN ABS(
      (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_001_gross_sales)
      - (SELECT SUM(line_sales_value_pretax) FROM aistra_ayush.silver.transactions
         WHERE line_sales_value_pretax IS NOT NULL)
    ) < 0.01 THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
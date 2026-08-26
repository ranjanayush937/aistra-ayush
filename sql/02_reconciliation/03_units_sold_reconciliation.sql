-- ============================================================
-- Reconciliation: KPI-003 Units Sold vs Silver Transactions
-- Purpose: Verify that Gold KPI-003 total units matches an
--   independently calculated sum from Silver transactions.
--   Note: 50% of transactions have NULL qty; both Gold and Silver
--   sums use the same filter (qty IS NOT NULL), so they should match.
-- Gold Source: aistra_ayush.gold.kpi_003_units_sold_eaches
-- Silver Source: aistra_ayush.silver.transactions
-- Pass condition: difference = 0
-- ============================================================

SELECT
  'KPI-003 vs Silver' AS reconciliation_check,
  (SELECT SUM(metric_value)
   FROM aistra_ayush.gold.kpi_003_units_sold_eaches) AS kpi_003_total_eaches,
  (SELECT SUM(qty)
   FROM aistra_ayush.silver.transactions
   WHERE qty IS NOT NULL) AS silver_total_qty,
  (SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_003_units_sold_eaches)
  - (SELECT SUM(qty) FROM aistra_ayush.silver.transactions WHERE qty IS NOT NULL)
    AS difference,
  CASE
    WHEN (
      SELECT SUM(metric_value) FROM aistra_ayush.gold.kpi_003_units_sold_eaches
    ) = (
      SELECT SUM(qty) FROM aistra_ayush.silver.transactions WHERE qty IS NOT NULL
    ) THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
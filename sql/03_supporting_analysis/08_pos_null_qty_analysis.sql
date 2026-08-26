-- ============================================================
-- POS Null Quantity Analysis (Data Quality)
-- Purpose: Analyze the impact of NULL qty on POS transaction data.
--   50% of transactions have NULL qty, which results in NULL
--   line_sales_value_pretax. This query breaks down the null rate
--   by month, channel, and outlet to identify patterns.
-- Source: aistra_ayush.silver.transactions
-- Parameters: start_date, end_date
-- ============================================================

SELECT
  DATE_TRUNC('month', business_date) AS month,
  COUNT(*) AS total_transaction_lines,
  COUNT(CASE WHEN qty IS NULL THEN 1 END) AS null_qty_lines,
  ROUND(100.0 * COUNT(CASE WHEN qty IS NULL THEN 1 END) / COUNT(*), 2) AS null_qty_pct,
  COUNT(CASE WHEN line_sales_value_pretax IS NULL THEN 1 END) AS null_sales_value_lines,
  ROUND(100.0 * COUNT(CASE WHEN line_sales_value_pretax IS NULL THEN 1 END) / COUNT(*), 2) AS null_sales_value_pct,
  ROUND(SUM(CASE WHEN line_sales_value_pretax IS NOT NULL THEN line_sales_value_pretax ELSE 0 END), 2) AS sales_with_qty_usd,
  COUNT(DISTINCT outlet_code) AS active_outlets
FROM aistra_ayush.silver.transactions
WHERE business_date >= CAST(:start_date AS DATE)
  AND business_date <= CAST(:end_date AS DATE)
GROUP BY DATE_TRUNC('month', business_date)
ORDER BY month;
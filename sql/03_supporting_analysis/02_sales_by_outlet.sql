-- ============================================================
-- Sales by Outlet with Channel Attribution
-- Purpose: Show total sales, transaction count, and effective channel
--   per outlet for the selected period. Uses Silver transactions with
--   SCD Type 2 outlet join for historically accurate channel.
-- Source: aistra_ayush.silver.transactions + aistra_ayush.silver.outlets
-- Parameters: start_date, end_date, channel
-- ============================================================

SELECT
  t.outlet_code,
  o.channel AS effective_channel,
  COUNT(*) AS transaction_line_count,
  ROUND(SUM(t.line_sales_value_pretax), 2) AS total_sales_usd,
  ROUND(AVG(t.line_sales_value_pretax), 2) AS avg_line_value_usd,
  MIN(t.business_date) AS first_sale_date,
  MAX(t.business_date) AS last_sale_date
FROM aistra_ayush.silver.transactions t
INNER JOIN aistra_ayush.silver.outlets o
  ON t.outlet_code = o.outlet_code
  AND t.business_date >= o.effective_from
  AND (t.business_date < o.effective_to OR o.effective_to IS NULL)
WHERE t.line_sales_value_pretax IS NOT NULL
  AND t.business_date >= CAST(:start_date AS DATE)
  AND t.business_date <= CAST(:end_date AS DATE)
  AND (:channel = 'ALL' OR o.channel = :channel)
GROUP BY t.outlet_code, o.channel
ORDER BY total_sales_usd DESC;
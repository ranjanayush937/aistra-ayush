-- ============================================================
-- Reconciliation: KPI-012 Order-to-POS vs Silver Independently
-- Purpose: Verify that Gold KPI-012 monthly order and POS totals
--   match independently calculated sums from Silver sales_orders
--   and Silver transactions. Checks both value and count per month.
-- Gold Source: aistra_ayush.gold.kpi_012_order_pos_reconciliation
-- Silver Sources:
--   aistra_ayush.silver.sales_orders
--   aistra_ayush.silver.transactions
-- Pass condition: all months show zero difference
-- ============================================================

WITH silver_monthly AS (
  SELECT
    COALESCE(o.month, p.month) AS month,
    COALESCE(o.total_order_value, 0) AS silver_order_value,
    COALESCE(o.order_count, 0) AS silver_order_count,
    COALESCE(p.total_pos_value, 0) AS silver_pos_value,
    COALESCE(p.transaction_count, 0) AS silver_transaction_count
  FROM (
    SELECT DATE_TRUNC('month', order_date) AS month,
           SUM(order_value_gross) AS total_order_value,
           COUNT(*) AS order_count
    FROM aistra_ayush.silver.sales_orders
    WHERE order_value_gross IS NOT NULL
    GROUP BY DATE_TRUNC('month', order_date)
  ) o
  FULL OUTER JOIN (
    SELECT DATE_TRUNC('month', business_date) AS month,
           SUM(line_sales_value_pretax) AS total_pos_value,
           COUNT(*) AS transaction_count
    FROM aistra_ayush.silver.transactions
    WHERE line_sales_value_pretax IS NOT NULL
    GROUP BY DATE_TRUNC('month', business_date)
  ) p ON o.month = p.month
),
gold_monthly AS (
  SELECT
    period_start AS month,
    order_value AS gold_order_value,
    order_count AS gold_order_count,
    pos_value AS gold_pos_value,
    transaction_count AS gold_transaction_count
  FROM aistra_ayush.gold.kpi_012_order_pos_reconciliation
)
SELECT
  g.month,
  ROUND(g.gold_order_value, 2) AS gold_order_value,
  ROUND(s.silver_order_value, 2) AS silver_order_value,
  ROUND(g.gold_order_value - s.silver_order_value, 2) AS order_value_diff,
  g.gold_order_count AS gold_order_count,
  s.silver_order_count AS silver_order_count,
  g.gold_order_count - s.silver_order_count AS order_count_diff,
  ROUND(g.gold_pos_value, 2) AS gold_pos_value,
  ROUND(s.silver_pos_value, 2) AS silver_pos_value,
  ROUND(g.gold_pos_value - s.silver_pos_value, 2) AS pos_value_diff,
  g.gold_transaction_count AS gold_txn_count,
  s.silver_transaction_count AS silver_txn_count,
  g.gold_transaction_count - s.silver_transaction_count AS txn_count_diff,
  CASE
    WHEN ABS(g.gold_order_value - s.silver_order_value) < 0.01
     AND g.gold_order_count = s.silver_order_count
     AND ABS(g.gold_pos_value - s.silver_pos_value) < 0.01
     AND g.gold_transaction_count = s.silver_transaction_count
    THEN 'PASS'
    ELSE 'FAIL'
  END AS status
FROM gold_monthly g
INNER JOIN silver_monthly s ON g.month = s.month
ORDER BY g.month;
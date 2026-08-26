-- ============================================================
-- KPI-012: Order-to-POS Value Reconciliation (Monthly)
-- Business Definition: Difference between governed order-header
--   value and POS sales value for each month. Orders and POS may
--   represent different business events/populations; a non-zero
--   variance is diagnostic, not automatically a data defect.
-- Grain: month
-- Metric: metric_value = order_value - pos_value
-- Unit: USD
-- Source: aistra_ayush.gold.kpi_012_order_pos_reconciliation
-- Filters: Full outer join of monthly orders and POS totals
-- Parameters: start_date, end_date
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  ROUND(order_value, 2) AS order_value_usd,
  ROUND(pos_value, 2) AS pos_value_usd,
  ROUND(metric_value, 2) AS variance_usd,
  metric_unit,
  variance_pct,
  order_count,
  transaction_count,
  calculated_at
FROM aistra_ayush.gold.kpi_012_order_pos_reconciliation
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
ORDER BY month_start;
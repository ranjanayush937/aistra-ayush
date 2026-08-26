-- ============================================================
-- KPI-002: Gross Sales by Channel (Daily)
-- Business Definition: Daily POS sales grouped by the outlet channel
--   applicable on the transaction date, using SCD Type 2 outlet master.
-- Grain: business_date, channel (daily, per channel)
-- Metric: metric_value = SUM(line_sales_value_pretax) per channel
-- Unit: USD
-- Source: aistra_ayush.gold.kpi_002_sales_by_channel
-- Filters: Point-in-time channel join; excludes NULL sales values
-- Parameters: start_date, end_date, channel
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS business_date,
  period_end,
  grain,
  dimension_channel AS channel,
  ROUND(metric_value, 2) AS gross_sales_usd,
  metric_unit,
  source_row_count AS transaction_line_count,
  calculated_at
FROM aistra_ayush.gold.kpi_002_sales_by_channel
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:channel = 'ALL' OR dimension_channel = :channel)
ORDER BY business_date, channel;
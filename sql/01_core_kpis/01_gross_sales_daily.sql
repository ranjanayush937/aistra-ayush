-- ============================================================
-- KPI-001: Gross Sales (Daily)
-- Business Definition: Total POS line sales value (pretax)
--   for each business date, after transaction-level deduplication.
-- Grain: business_date (daily)
-- Metric: metric_value = SUM(line_sales_value_pretax)
-- Unit: USD
-- Source: aistra_ayush.gold.kpi_001_gross_sales
-- Parameters: start_date, end_date
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS business_date,
  period_end,
  grain,
  ROUND(metric_value, 2) AS gross_sales_usd,
  metric_unit,
  source_row_count AS transaction_line_count,
  null_value_count,
  calculated_at
FROM aistra_ayush.gold.kpi_001_gross_sales
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
ORDER BY business_date;
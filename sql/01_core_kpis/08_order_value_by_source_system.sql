-- ============================================================
-- KPI-009: Order Value by Source System (Monthly)
-- Business Definition: Sum of order-header value by source system,
--   preserving source-system identity. Source systems may not be
--   economically comparable (different currencies/definitions).
-- Grain: month, source_system
-- Metric: metric_value = SUM(order_value_gross)
-- Unit: USD
-- Source: aistra_ayush.gold.kpi_009_order_value_by_system
-- Filters: Excludes NULL order values
-- Parameters: start_date, end_date, source_system
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  dimension_source_system AS source_system,
  ROUND(metric_value, 2) AS order_value_usd,
  metric_unit,
  source_row_count AS order_count,
  calculated_at
FROM aistra_ayush.gold.kpi_009_order_value_by_system
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:source_system = 'ALL' OR dimension_source_system = :source_system)
ORDER BY month_start, source_system;
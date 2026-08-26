-- ============================================================
-- Order Value Trend by Source System (Monthly)
-- Purpose: Show monthly order value and order count per source system
--   with month-over-month growth. Source systems are NOT combined
--   as they may not be economically comparable.
-- Source: aistra_ayush.gold.kpi_009_order_value_by_system
-- Parameters: start_date, end_date, source_system
-- ============================================================

SELECT
  period_start AS month_start,
  dimension_source_system AS source_system,
  ROUND(metric_value, 2) AS order_value_usd,
  source_row_count AS order_count,
  LAG(ROUND(metric_value, 2)) OVER (
    PARTITION BY dimension_source_system ORDER BY period_start
  ) AS prev_month_value_usd,
  ROUND(
    100.0 * (metric_value - LAG(metric_value) OVER (
      PARTITION BY dimension_source_system ORDER BY period_start
    )) / NULLIF(
      LAG(metric_value) OVER (
        PARTITION BY dimension_source_system ORDER BY period_start
      ), 0
    ),
    2
  ) AS mom_growth_pct
FROM aistra_ayush.gold.kpi_009_order_value_by_system
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:source_system = 'ALL' OR dimension_source_system = :source_system)
ORDER BY month_start, source_system;
-- ============================================================
-- KPI-005: Temperature Excursion Rate (Monthly)
-- Business Definition: Percentage of valid reefer telemetry readings
--   exceeding the chilled temperature threshold (> 8°C).
--   Readings with missing temperature are excluded from the denominator
--   and reported separately as data-quality exceptions.
-- Grain: month
-- Metric: metric_value = % of readings with temp_celsius > 8.0
-- Unit: PERCENT
-- Source: aistra_ayush.gold.kpi_005_temp_excursion_rate
-- Filters: Excludes readings with is_missing_temp = TRUE
-- Parameters: start_date, end_date
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  total_readings,
  excursions,
  metric_value AS excursion_rate_pct,
  metric_unit,
  source_row_count,
  calculated_at
FROM aistra_ayush.gold.kpi_005_temp_excursion_rate
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
ORDER BY month_start;
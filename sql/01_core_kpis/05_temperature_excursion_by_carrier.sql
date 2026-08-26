-- ============================================================
-- KPI-006: Temperature Excursion Rate by Carrier (Monthly)
-- Business Definition: Temperature excursion rate segmented by
--   telemetry vendor (proxy for carrier), to identify carrier-level
--   cold-chain performance.
-- Grain: month, telemetry_vendor
-- Metric: metric_value = % of readings with temp_celsius > 8.0 per vendor
-- Unit: PERCENT
-- Source: aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
-- Filters: Excludes readings with is_missing_temp = TRUE and
--   telemetry_vendor IS NULL
-- Parameters: start_date, end_date, carrier
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  dimension_vendor AS carrier,
  total_readings,
  excursions,
  metric_value AS excursion_rate_pct,
  metric_unit,
  source_row_count,
  calculated_at
FROM aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:carrier = 'ALL' OR dimension_vendor = :carrier)
ORDER BY month_start, carrier;
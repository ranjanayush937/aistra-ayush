-- ============================================================
-- Temperature Excursion Rate Trend by Month and Carrier
-- Purpose: Show monthly excursion rates for all carriers side-by-side
--   to compare cold-chain performance over time. Also includes the
--   overall monthly rate for context.
-- Source: aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
--         aistra_ayush.gold.kpi_005_temp_excursion_rate
-- Parameters: start_date, end_date
-- ============================================================

WITH carrier_monthly AS (
  SELECT
    period_start AS month_start,
    dimension_vendor AS carrier,
    metric_value AS excursion_rate_pct,
    total_readings,
    excursions
  FROM aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
  WHERE period_start >= CAST(:start_date AS DATE)
    AND period_start <= CAST(:end_date AS DATE)
),
overall_monthly AS (
  SELECT
    period_start AS month_start,
    metric_value AS overall_excursion_rate_pct,
    total_readings AS overall_total_readings
  FROM aistra_ayush.gold.kpi_005_temp_excursion_rate
  WHERE period_start >= CAST(:start_date AS DATE)
    AND period_start <= CAST(:end_date AS DATE)
)
SELECT
  c.month_start,
  o.overall_excursion_rate_pct,
  o.overall_total_readings,
  ROUND(MAX(CASE WHEN c.carrier = 'THERMLOG' THEN c.excursion_rate_pct END), 2) AS thermlog_rate_pct,
  ROUND(MAX(CASE WHEN c.carrier = 'COLDEYE' THEN c.excursion_rate_pct END), 2) AS coldeye_rate_pct,
  MAX(CASE WHEN c.carrier = 'THERMLOG' THEN c.excursions END) AS thermlog_excursions,
  MAX(CASE WHEN c.carrier = 'COLDEYE' THEN c.excursions END) AS coldeye_excursions
FROM carrier_monthly c
INNER JOIN overall_monthly o ON c.month_start = o.month_start
GROUP BY c.month_start, o.overall_excursion_rate_pct, o.overall_total_readings
ORDER BY c.month_start;
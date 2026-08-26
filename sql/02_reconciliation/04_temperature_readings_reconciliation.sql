-- ============================================================
-- Reconciliation: KPI-005 Temperature Readings vs Silver Telemetry
-- Purpose: Verify that the total readings counted in Gold KPI-005
--   matches the count of valid (non-missing) temperature readings in
--   Silver reefer_telemetry. A mismatch would indicate the Gold
--   pipeline is incorrectly including or excluding readings.
-- Gold Source: aistra_ayush.gold.kpi_005_temp_excursion_rate
-- Silver Source: aistra_ayush.silver.reefer_telemetry
-- Pass condition: counts match exactly
-- ============================================================

SELECT
  'KPI-005 readings vs Silver' AS reconciliation_check,
  (SELECT SUM(total_readings)
   FROM aistra_ayush.gold.kpi_005_temp_excursion_rate) AS kpi_005_total_readings,
  (SELECT COUNT(*)
   FROM aistra_ayush.silver.reefer_telemetry
   WHERE is_missing_temp = FALSE) AS silver_valid_readings,
  (SELECT SUM(total_readings) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate)
  - (SELECT COUNT(*) FROM aistra_ayush.silver.reefer_telemetry
     WHERE is_missing_temp = FALSE) AS difference,
  CASE
    WHEN (
      SELECT SUM(total_readings) FROM aistra_ayush.gold.kpi_005_temp_excursion_rate
    ) = (
      SELECT COUNT(*) FROM aistra_ayush.silver.reefer_telemetry
      WHERE is_missing_temp = FALSE
    ) THEN 'PASS'
    ELSE 'FAIL'
  END AS status;
-- ============================================================
-- KPI-010: Feed Data Completeness (Monthly by Feed)
-- Business Definition: Percentage of expected feed business dates/
--   partitions that contain received data for the selected period.
--   Missing partitions are exceptions, not zero-valued metrics.
-- Grain: month, feed_name
-- Metric: metric_value = (received_days / expected_days) * 100
-- Unit: PERCENT
-- Source: aistra_ayush.gold.kpi_010_feed_completeness
-- Note: This KPI table is currently a template. Actual implementation
--   requires querying Bronze table partitions and joining with the
--   ingestion manifest (expected_partitions.csv). The received_days
--   column is a placeholder (0) until Bronze metadata is integrated.
-- Parameters: start_date, end_date, feed_name
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS month_start,
  period_end AS month_end,
  grain,
  dimension_feed AS feed_name,
  expected_days,
  received_days,
  metric_value AS completeness_pct,
  metric_unit,
  missing_days,
  calculated_at
FROM aistra_ayush.gold.kpi_010_feed_completeness
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:feed_name = 'ALL' OR dimension_feed = :feed_name)
ORDER BY month_start, feed_name;
-- ============================================================
-- Top Products by Units Sold (Eaches)
-- Purpose: Rank products by total units sold in eaches for the
--   selected period. Includes product name and category for
--   business consumption.
-- Source: aistra_ayush.gold.kpi_003_units_sold_eaches
-- Parameters: start_date, end_date, category
-- ============================================================

SELECT
  dimension_sku AS sku_code,
  dimension_product_name AS product_name,
  dimension_category AS category,
  SUM(metric_value) AS total_units_eaches,
  SUM(source_row_count) AS transaction_line_count,
  DENSE_RANK() OVER (ORDER BY SUM(metric_value) DESC) AS unit_rank
FROM aistra_ayush.gold.kpi_003_units_sold_eaches
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND metric_value IS NOT NULL
  AND (:category = 'ALL' OR dimension_category = :category)
GROUP BY dimension_sku, dimension_product_name, dimension_category
ORDER BY total_units_eaches DESC
LIMIT 50;
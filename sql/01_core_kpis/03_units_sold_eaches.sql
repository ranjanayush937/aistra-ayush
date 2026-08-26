-- ============================================================
-- KPI-003: Units Sold (Eaches) (Daily by SKU)
-- Business Definition: Total quantity sold in eaches per business date
--   per SKU. Quantity is summed from POS transaction lines.
--   Note: 50% of transactions have NULL qty (source data issue);
--   these rows are retained with NULL metric_value, not converted to zero.
-- Grain: business_date, sku_code (daily, per SKU)
-- Metric: metric_value = SUM(qty)
-- Unit: EACHES
-- Source: aistra_ayush.gold.kpi_003_units_sold_eaches
-- Filters: Excludes NULL qty (retained as separate count); joins to
--   silver.products for product name and category.
-- Parameters: start_date, end_date, sku_code
-- ============================================================

SELECT
  kpi_id,
  kpi_name,
  period_start AS business_date,
  period_end,
  grain,
  dimension_sku AS sku_code,
  dimension_product_name AS product_name,
  dimension_category AS category,
  metric_value AS units_sold_eaches,
  metric_unit,
  source_row_count AS transaction_line_count,
  null_qty_count,
  calculated_at
FROM aistra_ayush.gold.kpi_003_units_sold_eaches
WHERE period_start >= CAST(:start_date AS DATE)
  AND period_start <= CAST(:end_date AS DATE)
  AND (:sku_code = 'ALL' OR dimension_sku = :sku_code)
ORDER BY business_date DESC, sku_code;
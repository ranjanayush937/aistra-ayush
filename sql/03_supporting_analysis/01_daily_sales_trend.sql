-- ============================================================
-- Daily Sales Trend with Month-over-Month Comparison
-- Purpose: Show daily gross sales with rolling 7-day average and
--   month-over-month growth rate for trend analysis.
-- Source: aistra_ayush.gold.kpi_001_gross_sales
-- Parameters: start_date, end_date
-- ============================================================

WITH daily AS (
  SELECT
    period_start AS business_date,
    metric_value AS gross_sales_usd
  FROM aistra_ayush.gold.kpi_001_gross_sales
  WHERE period_start >= CAST(:start_date AS DATE)
    AND period_start <= CAST(:end_date AS DATE)
),
with_rolling AS (
  SELECT
    business_date,
    ROUND(gross_sales_usd, 2) AS gross_sales_usd,
    ROUND(AVG(gross_sales_usd) OVER (ORDER BY business_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 2) AS rolling_7day_avg_usd
  FROM daily
),
monthly AS (
  SELECT
    DATE_TRUNC('month', business_date) AS month,
    SUM(gross_sales_usd) AS month_total
  FROM daily
  GROUP BY DATE_TRUNC('month', business_date)
)
SELECT
  r.business_date,
  r.gross_sales_usd,
  r.rolling_7day_avg_usd,
  DATE_TRUNC('month', r.business_date) AS month,
  m.month_total AS monthly_sales_usd,
  LAG(m.month_total) OVER (ORDER BY m.month) AS prev_month_sales_usd,
  ROUND(
    100.0 * (m.month_total - LAG(m.month_total) OVER (ORDER BY m.month))
    / NULLIF(LAG(m.month_total) OVER (ORDER BY m.month), 0),
    2
  ) AS mom_growth_pct
FROM with_rolling r
LEFT JOIN monthly m ON DATE_TRUNC('month', r.business_date) = m.month
ORDER BY r.business_date;
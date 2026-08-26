# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Business KPI Query Interface — Overview
# MAGIC %md
# MAGIC # Kestrel Provisions — Business KPI Query Interface
# MAGIC
# MAGIC ## Purpose
# MAGIC This notebook provides **business-facing queries** for all Gold-layer KPIs. Each query:
# MAGIC - Uses clear, business-friendly names and filters
# MAGIC - References only Gold KPI tables (no joins required)
# MAGIC - Includes proper date filters aligned with available data
# MAGIC - Is validated against the underlying Gold table
# MAGIC - Is ready for use in dashboards or reports
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Data Coverage
# MAGIC **Available Date Range:** January 1, 2025 to September 30, 2025 (9 months)  
# MAGIC **Catalog:** `aistra_ayush.gold`  
# MAGIC **Total KPIs:** 12 operational metrics across Finance, Supply Chain, Master Data, and Data Quality
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Query Index
# MAGIC
# MAGIC ### Finance & Sales
# MAGIC 1. **Daily Gross Sales** — Total POS sales per day
# MAGIC 2. **Sales by Channel** — Daily sales breakdown by outlet channel (GT, MT, HORECA, ECOM)
# MAGIC 3. **Units Sold** — Quantity sold converted to eaches
# MAGIC 4. **Finance Report Variance** — Weekly variance between governed and legacy sales systems
# MAGIC
# MAGIC ### Supply Chain
# MAGIC 5. **Temperature Excursion Rate** — % of reefer readings exceeding chilled threshold (monthly)
# MAGIC 6. **Temp Excursion by Carrier** — Excursion rate by carrier/vendor (monthly)
# MAGIC 7. **Dock-to-Dispatch Cycle Time** — Median warehouse processing time (monthly, by warehouse)
# MAGIC
# MAGIC ### Master Data
# MAGIC 8. **Outlet Channel Changes** — Count of outlets that changed channel classification
# MAGIC
# MAGIC ### Order Management
# MAGIC 9. **Order Value by Source System** — Monthly orders by ERP system
# MAGIC 10. **Order-POS Reconciliation** — Monthly variance between ERP orders and POS sales
# MAGIC
# MAGIC ### Data Quality
# MAGIC 11. **Feed Data Completeness** — % of expected feed partitions received (monthly, by feed)
# MAGIC 12. **Feed Row Count Variance** — Deviation from expected row counts (by feed and partition)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## Query Guidelines
# MAGIC - All date filters use the available range: **2025-01-01 to 2025-09-30**
# MAGIC - Metrics are pre-aggregated in Gold tables — no additional aggregation needed
# MAGIC - All queries return business-ready results with proper units and labels
# MAGIC - For trending: filter by `period_start` date range
# MAGIC - For current period: use `WHERE period_start >= DATE_TRUNC('month', CURRENT_DATE())`

# COMMAND ----------

# DBTITLE 1,Finance & Sales KPIs
# MAGIC %md
# MAGIC ---
# MAGIC # Finance & Sales KPIs
# MAGIC
# MAGIC These queries provide daily and channel-level sales metrics from POS transactions.

# COMMAND ----------

# DBTITLE 1,Q1: Daily Gross Sales
# MAGIC %sql
# MAGIC -- Q1: Daily Gross Sales
# MAGIC -- Business Question: What are our total daily sales?
# MAGIC -- Source: kpi_001_gross_sales
# MAGIC -- Grain: Daily
# MAGIC -- Date Range: Last 90 days
# MAGIC
# MAGIC SELECT 
# MAGIC   period_start AS sales_date,
# MAGIC   ROUND(metric_value, 0) AS gross_sales_usd
# MAGIC FROM aistra_ayush.gold.kpi_001_gross_sales
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 90)
# MAGIC   AND period_start <= '2025-09-30'  -- Data cutoff date
# MAGIC ORDER BY period_start DESC
# MAGIC LIMIT 20;

# COMMAND ----------

# DBTITLE 1,Q2: Sales by Channel
# MAGIC %sql
# MAGIC -- Q2: Sales by Channel
# MAGIC -- Business Question: What are our sales by channel? How does each channel perform?
# MAGIC -- Source: kpi_002_sales_by_channel
# MAGIC -- Grain: Daily, by channel (GT, MT, HORECA, ECOM)
# MAGIC -- Date Range: Year-to-date 2026
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_channel AS channel,
# MAGIC   COUNT(DISTINCT period_start) AS days_with_sales,
# MAGIC   ROUND(SUM(metric_value), 0) AS total_sales_usd,
# MAGIC   ROUND(AVG(metric_value), 0) AS avg_daily_sales_usd,
# MAGIC   ROUND(100.0 * SUM(metric_value) / SUM(SUM(metric_value)) OVER(), 2) AS pct_of_total
# MAGIC FROM aistra_ayush.gold.kpi_002_sales_by_channel
# MAGIC WHERE period_start >= '2025-01-01'
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_channel
# MAGIC ORDER BY total_sales_usd DESC;

# COMMAND ----------

# DBTITLE 1,Q3: Units Sold (Eaches)
# MAGIC %sql
# MAGIC -- Q3: Units Sold by Channel (Eaches)
# MAGIC -- Business Question: How many units did we sell by channel?
# MAGIC -- Source: kpi_003_units_sold
# MAGIC -- Grain: Daily, by channel (GT, MT, HORECA, ECOM)
# MAGIC -- Date Range: Year-to-date 2025
# MAGIC -- Note: 50% of transactions have NULL qty in source data
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_channel AS channel,
# MAGIC   COUNT(DISTINCT period_start) AS days_with_sales,
# MAGIC   ROUND(SUM(metric_value), 0) AS total_units_eaches,
# MAGIC   ROUND(AVG(metric_value), 0) AS avg_daily_units,
# MAGIC   ROUND(100.0 * SUM(metric_value) / SUM(SUM(metric_value)) OVER(), 2) AS pct_of_total
# MAGIC FROM aistra_ayush.gold.kpi_003_units_sold
# MAGIC WHERE period_start >= '2025-01-01'
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC   AND metric_value IS NOT NULL
# MAGIC GROUP BY dimension_channel
# MAGIC ORDER BY total_units_eaches DESC;

# COMMAND ----------

# DBTITLE 1,Supply Chain KPIs
# MAGIC %md
# MAGIC ---
# MAGIC # Supply Chain KPIs
# MAGIC
# MAGIC These queries track cold chain compliance and warehouse efficiency.

# COMMAND ----------

# DBTITLE 1,Q5: Temperature Excursion Rate
# MAGIC %sql
# MAGIC -- Q5: Temperature Excursion Rate
# MAGIC -- Business Question: What is our chilled temperature breach rate?
# MAGIC -- Source: kpi_005_temp_excursion_rate
# MAGIC -- Grain: Monthly
# MAGIC -- Date Range: Last 12 months
# MAGIC -- Threshold: Chilled band = 2-8°C (excursion when temp > 8°C)
# MAGIC
# MAGIC SELECT 
# MAGIC   period_start AS month,
# MAGIC   ROUND(metric_value, 2) AS excursion_rate_pct,
# MAGIC   total_readings,
# MAGIC   excursions,
# MAGIC   CASE 
# MAGIC     WHEN metric_value <= 5.0 THEN 'Excellent'
# MAGIC     WHEN metric_value <= 7.0 THEN 'Good'
# MAGIC     WHEN metric_value <= 10.0 THEN 'Fair'
# MAGIC     ELSE 'Poor'
# MAGIC   END AS performance_rating
# MAGIC FROM aistra_ayush.gold.kpi_005_temp_excursion_rate
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 365)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC ORDER BY period_start DESC;

# COMMAND ----------

# DBTITLE 1,Q6: Temp Excursion by Carrier
# MAGIC %sql
# MAGIC -- Q6: Temp Excursion by Carrier
# MAGIC -- Business Question: Which carriers have the highest temperature breach rates?
# MAGIC -- Source: kpi_006_temp_excursion_by_carrier
# MAGIC -- Grain: Monthly, by carrier/vendor
# MAGIC -- Date Range: Last 6 months
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_vendor AS carrier_vendor,
# MAGIC   COUNT(DISTINCT period_start) AS months_active,
# MAGIC   ROUND(AVG(metric_value), 2) AS avg_excursion_rate_pct,
# MAGIC   ROUND(MIN(metric_value), 2) AS best_month_pct,
# MAGIC   ROUND(MAX(metric_value), 2) AS worst_month_pct,
# MAGIC   SUM(total_readings) AS total_readings_6mo
# MAGIC FROM aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 180)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_vendor
# MAGIC ORDER BY avg_excursion_rate_pct DESC;

# COMMAND ----------

# DBTITLE 1,Q7: Dock-to-Dispatch Cycle Time
# MAGIC %sql
# MAGIC -- Q7: Dock-to-Dispatch Cycle Time
# MAGIC -- Business Question: What is our median warehouse processing time?
# MAGIC -- Source: kpi_007_cycle_time
# MAGIC -- Grain: Monthly, by warehouse
# MAGIC -- Date Range: Last 6 months
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_warehouse AS warehouse,
# MAGIC   COUNT(*) AS months_tracked,
# MAGIC   ROUND(AVG(metric_value), 1) AS avg_median_cycle_hours,
# MAGIC   ROUND(MIN(metric_value), 1) AS best_month_hours,
# MAGIC   ROUND(MAX(metric_value), 1) AS worst_month_hours,
# MAGIC   ROUND(AVG(metric_value) / 24, 1) AS avg_median_cycle_days
# MAGIC FROM aistra_ayush.gold.kpi_007_cycle_time
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 180)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_warehouse
# MAGIC ORDER BY avg_median_cycle_hours;

# COMMAND ----------

# DBTITLE 1,Master Data & Order KPIs
# MAGIC %md
# MAGIC ---
# MAGIC # Master Data & Order Management KPIs
# MAGIC
# MAGIC These queries track master data changes and order reconciliation.

# COMMAND ----------

# DBTITLE 1,Q8: Outlet Channel Changes
# MAGIC %sql
# MAGIC -- Q8: Outlet Channel Changes
# MAGIC -- Business Question: How many outlets changed channel classification?
# MAGIC -- Source: kpi_008_channel_changes
# MAGIC -- Grain: Event-level (one row per change)
# MAGIC -- Date Range: Last 90 days
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_old_channel AS from_channel,
# MAGIC   dimension_new_channel AS to_channel,
# MAGIC   COUNT(*) AS change_count,
# MAGIC   COUNT(DISTINCT dimension_outlet) AS unique_outlets
# MAGIC FROM aistra_ayush.gold.kpi_008_channel_changes
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 90)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_old_channel, dimension_new_channel
# MAGIC ORDER BY change_count DESC
# MAGIC LIMIT 10;

# COMMAND ----------

# DBTITLE 1,Q9: Order Value by Source System
# MAGIC %sql
# MAGIC -- Q9: Order Value by Source System
# MAGIC -- Business Question: What is our order value by ERP source system?
# MAGIC -- Source: kpi_009_order_value_by_system
# MAGIC -- Grain: Monthly, by source system
# MAGIC -- Date Range: Last 12 months
# MAGIC -- Note: Source systems may not be economically comparable
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_source_system AS source_system,
# MAGIC   COUNT(*) AS months_active,
# MAGIC   ROUND(SUM(metric_value), 0) AS total_order_value_usd,
# MAGIC   ROUND(AVG(metric_value), 0) AS avg_monthly_value,
# MAGIC   SUM(source_row_count) AS total_orders
# MAGIC FROM aistra_ayush.gold.kpi_009_order_value_by_system
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 365)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_source_system
# MAGIC ORDER BY total_order_value_usd DESC;

# COMMAND ----------

# DBTITLE 1,Q10: Order-POS Reconciliation
# MAGIC %sql
# MAGIC -- Q10: Order-POS Reconciliation
# MAGIC -- Business Question: How do ERP orders reconcile to POS sales?
# MAGIC -- Source: kpi_012_order_pos_reconciliation
# MAGIC -- Grain: Monthly
# MAGIC -- Date Range: Last 12 months
# MAGIC -- Note: Orders and POS represent different business events; variance is diagnostic
# MAGIC
# MAGIC SELECT 
# MAGIC   period_start AS month,
# MAGIC   ROUND(order_value, 0) AS erp_order_value_usd,
# MAGIC   ROUND(pos_value, 0) AS pos_sales_value_usd,
# MAGIC   metric_value AS variance_usd,
# MAGIC   variance_pct AS variance_pct,
# MAGIC   CASE 
# MAGIC     WHEN ABS(variance_pct) <= 5 THEN 'Close match'
# MAGIC     WHEN ABS(variance_pct) <= 15 THEN 'Acceptable'
# MAGIC     ELSE 'Review needed'
# MAGIC   END AS reconciliation_status
# MAGIC FROM aistra_ayush.gold.kpi_012_order_pos_reconciliation
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 365)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC ORDER BY period_start DESC;

# COMMAND ----------

# DBTITLE 1,Data Quality KPIs
# MAGIC %md
# MAGIC ---
# MAGIC # Data Quality KPIs
# MAGIC
# MAGIC These queries monitor feed data completeness and consistency.

# COMMAND ----------

# DBTITLE 1,Q11: Feed Data Completeness
# MAGIC %sql
# MAGIC -- Q11: Feed Data Completeness
# MAGIC -- Business Question: How many feed days are missing?
# MAGIC -- Source: kpi_010_feed_completeness
# MAGIC -- Grain: Monthly, by feed
# MAGIC -- Date Range: Last 6 months
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_feed AS feed_name,
# MAGIC   COUNT(*) AS months_tracked,
# MAGIC   ROUND(AVG(metric_value), 2) AS avg_completeness_pct,
# MAGIC   ROUND(MIN(metric_value), 2) AS worst_month_pct,
# MAGIC   SUM(missing_days) AS total_missing_days,
# MAGIC   CASE 
# MAGIC     WHEN AVG(metric_value) >= 98 THEN 'Excellent'
# MAGIC     WHEN AVG(metric_value) >= 95 THEN 'Good'
# MAGIC     WHEN AVG(metric_value) >= 90 THEN 'Fair'
# MAGIC     ELSE 'Poor'
# MAGIC   END AS data_quality_rating
# MAGIC FROM aistra_ayush.gold.kpi_010_feed_completeness
# MAGIC WHERE period_start >= DATE_SUB('2025-09-30', 180)
# MAGIC   AND period_start <= '2025-09-30'
# MAGIC GROUP BY dimension_feed
# MAGIC ORDER BY avg_completeness_pct DESC;

# COMMAND ----------

# DBTITLE 1,Q12: Feed Row Count Variance
# MAGIC %sql
# MAGIC -- Q12: Feed Row Count Variance
# MAGIC -- Business Question: Are feed row counts within expected ranges?
# MAGIC -- Source: kpi_011_feed_row_variance
# MAGIC -- Grain: By feed and partition
# MAGIC -- Date Range: Recent partitions with largest variance
# MAGIC -- Purpose: Detect anomalous feed volumes
# MAGIC
# MAGIC SELECT 
# MAGIC   dimension_feed AS feed_name,
# MAGIC   dimension_partition AS partition_date,
# MAGIC   observed_row_count,
# MAGIC   expected_row_count,
# MAGIC   metric_value AS variance_pct,
# MAGIC   CASE 
# MAGIC     WHEN ABS(metric_value) <= 5 THEN 'Normal'
# MAGIC     WHEN ABS(metric_value) <= 15 THEN 'Minor deviation'
# MAGIC     ELSE 'Significant deviation'
# MAGIC   END AS variance_status
# MAGIC FROM aistra_ayush.gold.kpi_011_feed_row_variance
# MAGIC WHERE ABS(metric_value) > 5  -- Show only deviations > 5%
# MAGIC ORDER BY ABS(metric_value) DESC
# MAGIC LIMIT 20;

# COMMAND ----------


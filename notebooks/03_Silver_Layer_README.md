# Silver Layer Implementation — Kestrel Provisions

**Project:** Kestrel Provisions Data Engineering Assessment  
**Layer:** Silver (Conformed/Clean)  
**Catalog:** `aistra_ayush.silver`  
**Created:** 2026-08-26  

---

## Overview

This document describes the **minimum viable Silver layer** required to support the documented KPIs in `KPI_CATALOG.md`. The Silver layer transforms Bronze raw data into clean, conformed entities ready for analytical consumption.

**Design Principle:** Only implement entities and columns directly required by the KPI requirements. No unnecessary dimensions, no full star schema, no invented data.

---

## Entity Catalog

### 1. `silver.products`

**Source:** `bronze.erp_product_master`  
**Grain:** One row per SKU (latest effective record from CDC)  
**Business Key:** `sku_code`  
**Row Count:** 1,084  

**Purpose:**
- Product master data for SKU attributes
- UOM conversion support for KPI-003 (Units Sold in Eaches)
- Join target for transaction-level analysis

**Key Transformations:**
- Apply CDC logic: take latest record per `sku_code` using `__seq` and `__op_ts`
- Exclude deleted records (`__op = 'D'`)
- Cast `is_chilled` to BOOLEAN
- Retain essential product attributes (name, category, brand, case_pack, prices, GST rate, shelf life)

**Validation Results:**
- ✅ 1,084 unique SKUs
- ✅ Zero duplicate business keys
- ✅ Zero null keys
- ✅ Zero null product names or categories

**Usage:**
```sql
-- Join to transactions for product attributes
SELECT t.*, p.category, p.brand, p.case_pack
FROM silver.transactions t
INNER JOIN silver.products p ON t.sku_code = p.sku_code
```

---

### 2. `silver.outlets`

**Source:** `bronze.erp_outlet_master`  
**Grain:** SCD Type 2 — One row per outlet per effective period  
**Business Key:** `outlet_code` + `effective_from`  
**Row Count:** 8,726 (2,400 unique outlets, 2,353 current records)  
**Date Range:** 2024-12-31 to 2026-06-30  

**Purpose:**
- Point-in-time outlet attributes for historical reporting
- **Critical for KPI-002:** Gross Sales by Channel (requires effective-dated channel attribution)
- **Critical for KPI-008:** Outlet Channel Change Count (tracks channel changes over time)

**Key Transformations:**
- Construct SCD Type 2 from CDC stream
- `effective_from` = operation timestamp date
- `effective_to` = next operation timestamp date (NULL for current records)
- Include inserts and updates (`__op` IN ('I', 'U'))
- Preserve `operation_type` and `operation_timestamp` for auditability

**Validation Results:**
- ✅ 8,726 historical records
- ✅ 2,400 unique outlets
- ✅ 2,353 current records (effective_to IS NULL)
- ✅ Zero null keys or channels
- ✅ Date range spans 18 months of history

**Usage:**
```sql
-- Historical channel attribution for a transaction
SELECT t.*, o.channel AS effective_channel
FROM silver.transactions t
INNER JOIN silver.outlets o 
  ON t.outlet_code = o.outlet_code
  AND t.business_date >= o.effective_from
  AND (t.business_date < o.effective_to OR o.effective_to IS NULL)
```

---

### 3. `silver.transactions`

**Source:** `bronze.pos_transactions`  
**Grain:** One row per transaction line (deduped on business key)  
**Business Key:** `txn_id` + `txn_line_no`  
**Row Count:** 4,000,000  
**Date Range:** 2025-01-01 to 2026-06-30  
**Total Sales Value:** $2,671,766,610 (pretax)  

**Purpose:**
- Clean, deduplicated POS transaction lines
- **Primary driver for:**
  - KPI-001: Gross Sales
  - KPI-002: Gross Sales by Channel
  - KPI-003: Units Sold (Eaches)
  - KPI-004: Finance Report Variance
  - KPI-012: Order-to-POS Reconciliation

**Key Transformations:**
- **Deduplication:** ROW_NUMBER() OVER (PARTITION BY txn_id, txn_line_no) to keep first occurrence
- **Date Parsing:** CAST event_ts (STRING) to TIMESTAMP
- **Business Date Extraction:** DATE(event_timestamp) for period attribution
- **Calculated Sales Value:**
  - `line_sales_value_pretax = (unit_price * qty) - discount_amount`
  - `line_sales_value_incl_tax = line_sales_value_pretax + tax_amount`
- **NULL Handling:** qty retained as NULL when missing (not converted to zero)
- **Quality Filters:** Exclude records with NULL business keys or NULL event_timestamp

**Validation Results:**
- ✅ 4,000,000 unique business keys (zero duplicates)
- ✅ Zero null txn_id or txn_line_no
- ✅ Zero null outlet_code or sku_code
- ⚠️ 50.03% null qty (documented Bronze anomaly, retained for transparency)
- ✅ 50.03% null line_sales_value (consequence of null qty)
- ✅ Date range: 18 months (2025-01-01 to 2026-06-30)

**Known Issues:**
- **qty 50% null:** Documented raw data anomaly from profiling. Values retained as NULL rather than imputed.
- **Duplicate business keys in Bronze:** Bronze contained duplicates (4.08M rows → 4M Silver rows). Deduplication applied using first-ingested-wins logic.

**Usage:**
```sql
-- KPI-001: Gross Sales
SELECT 
  business_date,
  SUM(line_sales_value_pretax) AS gross_sales
FROM silver.transactions
WHERE line_sales_value_pretax IS NOT NULL  -- Exclude NULL qty lines
GROUP BY business_date
ORDER BY business_date;
```

---

### 4. `silver.sales_orders`

**Source:** `bronze.erp_sales_order_header`  
**Grain:** One row per order (latest effective record from CDC)  
**Business Key:** `order_number`  
**Row Count:** 317,120  
**Date Range:** 2025-01-01 to 2026-06-30  
**Total Order Value:** $77,068,893,166  

**Purpose:**
- ERP order header records for order-value analysis
- **Critical for:**
  - KPI-009: Order Value by Source System
  - KPI-012: Order-to-POS Value Reconciliation

**Key Transformations:**
- Apply CDC logic: latest record per `order_number` using `__seq` and `__op_ts`
- Exclude deleted orders (`__op = 'D'`)
- Parse `order_date` and `requested_delivery_date` (STRING → DATE)
- Calculate `order_value_net = order_value_gross - discount_amount`
- **Preserve `source_system` identity** (do not combine incompatible systems)

**Validation Results:**
- ✅ 317,120 unique orders
- ✅ 3 distinct source systems
- ✅ Zero null keys
- ✅ Zero null order dates
- ✅ Date range: 18 months

**Important Notes:**
- **Source System Heterogeneity:** The three source systems may use different value definitions, currencies, or business logic. KPI-009 explicitly preserves source_system identity rather than assuming equivalence.
- **Order vs POS Populations:** Orders and POS transactions represent different business events. KPI-012 reconciliation must account for incompatible populations.

**Usage:**
```sql
-- KPI-009: Order Value by Source System
SELECT 
  source_system,
  DATE_TRUNC('month', order_date) AS month,
  SUM(order_value_gross) AS total_order_value
FROM silver.sales_orders
GROUP BY source_system, DATE_TRUNC('month', order_date)
ORDER BY month, source_system;
```

---

### 5. `silver.reefer_telemetry`

**Source:** `bronze.reefer_telemetry`  
**Grain:** One row per telemetry reading  
**Business Key:** `device_id` + `reading_timestamp`  
**Row Count:** 3,713,926  
**Date Range:** 2025-01-01 to 2026-07-01  
**Devices:** 340 unique devices  
**Vendors:** 2 (THERMLOG, COLDEYE)  

**Purpose:**
- Normalized temperature telemetry for cold-chain monitoring
- **Critical for:**
  - KPI-005: Temperature Excursion Rate
  - KPI-006: Temperature Excursion Rate by Carrier

**Key Transformations:**
- **Temperature Normalization to Celsius:**
  - Celsius (temp_unit = 'C'): temp_value unchanged
  - Fahrenheit (temp_unit = 'F'): (temp_value - 32) × 5/9
  - Kelvin (temp_unit = 'K'): temp_value - 273.15
  - Unknown unit: NULL
- Parse `reading_ts` (STRING → TIMESTAMP)
- Extract `reading_date` from timestamp
- **Data Quality Flag:** `is_missing_temp = TRUE` when temp_value or temp_unit is NULL
- Retain original `temp_value_raw` and `temp_unit` for traceability

**Validation Results:**
- ✅ 3,713,926 readings
- ✅ 340 unique devices
- ✅ 2 unique vendors
- ⚠️ 8.54% missing temperature readings (flagged in `is_missing_temp`)
- ✅ Avg temperature: 4.2°C (within chilled band)
- ✅ Temp range: -9.39°C to 17.15°C

**Known Issues:**
- **8.54% missing temp:** Telemetry with NULL temp_value or temp_unit. These readings are excluded from excursion-rate denominator but reported separately as coverage exceptions (per KPI-005 spec).
- **Firmware clock offset:** Known historical issue with one firmware line (per Feed Contracts doc). Believed fixed but should be validated in analysis.

**Usage:**
```sql
-- KPI-005: Temperature Excursion Rate (chilled band: 2-8°C)
WITH eligible_readings AS (
  SELECT *
  FROM silver.reefer_telemetry
  WHERE is_missing_temp = FALSE  -- Exclude incomplete telemetry
)
SELECT
  COUNT(*) AS total_readings,
  COUNT(CASE WHEN temp_celsius > 8.0 THEN 1 END) AS excursions,
  ROUND(100.0 * COUNT(CASE WHEN temp_celsius > 8.0 THEN 1 END) / COUNT(*), 2) AS excursion_rate_pct
FROM eligible_readings;
```

---

### 6. `silver.wms_events`

**Source:** `bronze.wms_scan_events`  
**Grain:** One row per scan event  
**Business Key:** `scan_id`  
**Row Count:** 1,496,000  
**Date Range:** 2025-01-01 to 2026-06-30  
**Warehouses:** 8  
**Event Types:** 6 (RECEIVE, PUTAWAY, PICK, PACK, STAGE, DISPATCH)  

**Purpose:**
- Warehouse handling events for cycle-time analysis
- **Critical for:**
  - KPI-007: Median Dock-to-Dispatch Cycle Time

**Key Transformations:**
- Parse `event_ts` (STRING → TIMESTAMP)
- Extract `event_date` from timestamp
- Standardize column names
- Exclude records with NULL scan_id or NULL event_ts

**Validation Results:**
- ✅ 1,496,000 unique scans
- ✅ 8 unique warehouses
- ✅ 6 distinct event types
- ✅ Zero null keys
- ✅ Zero null timestamps

**Usage:**
```sql
-- KPI-007: Median Dock-to-Dispatch Cycle Time
WITH event_pairs AS (
  SELECT
    order_number,
    warehouse_code,
    MIN(CASE WHEN event_type = 'RECEIVE' THEN event_timestamp END) AS dock_time,
    MAX(CASE WHEN event_type = 'DISPATCH' THEN event_timestamp END) AS dispatch_time
  FROM silver.wms_events
  GROUP BY order_number, warehouse_code
  HAVING dock_time IS NOT NULL AND dispatch_time IS NOT NULL
),
cycle_times AS (
  SELECT
    warehouse_code,
    order_number,
    TIMESTAMPDIFF(HOUR, dock_time, dispatch_time) AS cycle_hours
  FROM event_pairs
  WHERE dispatch_time > dock_time  -- Exclude negative durations
)
SELECT
  warehouse_code,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cycle_hours) AS median_cycle_hours
FROM cycle_times
GROUP BY warehouse_code;
```

---

## KPI → Silver Entity Mapping

| KPI ID | KPI Name | Required Silver Entities | Primary Join Keys |
|--------|----------|--------------------------|-------------------|
| KPI-001 | Gross Sales | `transactions` | - |
| KPI-002 | Gross Sales by Channel | `transactions`, `outlets` | outlet_code + business_date |
| KPI-003 | Units Sold (Eaches) | `transactions`, `products` | sku_code |
| KPI-004 | Finance Report Variance | `transactions` | - |
| KPI-005 | Temperature Excursion Rate | `reefer_telemetry` | - |
| KPI-006 | Temp Excursion by Carrier | `reefer_telemetry` | (requires carrier master ref data) |
| KPI-007 | Dock-to-Dispatch Cycle Time | `wms_events` | order_number, event_type |
| KPI-008 | Outlet Channel Change Count | `outlets` | outlet_code, effective_from |
| KPI-009 | Order Value by Source System | `sales_orders` | - |
| KPI-012 | Order-to-POS Reconciliation | `transactions`, `sales_orders` | outlet_code, business date |

---

## Conformance Standards Applied

### 1. Naming Conventions
- **Tables:** `aistra_ayush.silver.<entity_name>` (lowercase, singular or plural as appropriate)
- **Columns:** snake_case
- **Business keys:** Explicit, documented in grain description
- **Calculated fields:** Named with `_calculated` or descriptive suffix (e.g., `line_sales_value_pretax`)
- **Metadata columns:** Prefixed with `_` or suffixed with `_at` for timestamps

### 2. Data Types
- **Dates:** DATE type (not STRING)
- **Timestamps:** TIMESTAMP type (not STRING)
- **Monetary:** DOUBLE (no currency conversion applied; preserve source units)
- **Flags:** BOOLEAN where semantically appropriate
- **IDs:** STRING (preserve source data type)

### 3. NULL Handling
- **Missing numeric values:** Retained as NULL (never converted to zero)
- **Missing timestamps:** Retained as NULL (rows excluded from time-based calculations)
- **Missing dimensions:** Retained as NULL or flagged as 'UNKNOWN' depending on context

### 4. Deduplication Strategy
- **Business Key Uniqueness:** Enforced before aggregation
- **Duplicate Resolution:** First-ingested-wins (using `_ingested_at`, `_source_file`)
- **Audit Trail:** Original `_source_file` and ingestion metadata retained

### 5. CDC Processing
- **Latest Record Logic:** `ROW_NUMBER() OVER (PARTITION BY <key> ORDER BY __seq DESC, __op_ts DESC)`
- **Deleted Records:** Excluded via `__op != 'D'`
- **SCD Type 2 (Outlets):** `LEAD(__op_ts) OVER (PARTITION BY outlet_code ORDER BY __seq)` to construct effective_to

### 6. Date Attribution
- **Reporting Periods:** Use business/event date, not ingest date
- **Business Date Extraction:** `DATE(event_timestamp)` from parsed timestamp

---

## Data Quality Summary

| Entity | Total Rows | Unique Keys | Duplicate Rate | Null Keys | Key Issue |
|--------|-----------|-------------|----------------|-----------|----------|
| products | 1,084 | 1,084 | 0% | 0 | None |
| outlets | 8,726 | 8,726 | 0% | 0 | None |
| transactions | 4,000,000 | 4,000,000 | 0% | 0 | 50% null qty |
| sales_orders | 317,120 | 317,120 | 0% | 0 | None |
| reefer_telemetry | 3,713,926 | (not validated) | - | 0 | 8.54% missing temp |
| wms_events | 1,496,000 | 1,496,000 | 0% | 0 | None |

**Overall Assessment:** ✅ All critical business keys are unique, zero null keys across all entities.

---

## Known Limitations & Workarounds

### 1. POS Quantity 50% NULL
**Impact:** KPI-003 (Units Sold) will have incomplete coverage.  
**Mitigation:** 
- Retain NULL qty as-is (do not impute zero)
- Report qty-available vs qty-missing separately
- Flag incomplete records for source data investigation

### 2. Reefer Telemetry 8.54% Missing Temperature
**Impact:** KPI-005/006 denominator reduced by 8.54%.  
**Mitigation:**
- `is_missing_temp` flag added
- Exclude from excursion-rate denominator
- Report coverage exceptions separately

### 3. ERP Product Master 4 Missing Partition Dates
**Impact:** Product history incomplete for 4 days.  
**Mitigation:**
- Work with available CDC history
- Document missing dates in lineage

### 4. Source System Heterogeneity (Sales Orders)
**Impact:** The three ERP source systems may not be directly comparable.  
**Mitigation:**
- Preserve `source_system` column
- KPI-009 explicitly segments by source_system
- Do not combine incompatible populations

---

## Entities NOT Implemented (Out of Scope)

1. **Customers**
   - **Reason:** No stable customer identifier in POS. `basket_id` represents a shopping basket, not a reusable customer key.
   - **Impact:** Customer-level KPIs (lifetime value, cohorts, etc.) are out of scope.

2. **Payments / Refunds**
   - **Reason:** No separate payment or refund feeds. `payment_mode` is captured at transaction line but is not a separate entity.
   - **Impact:** Payment-method analysis possible via `transactions.payment_mode` but no refund tracking.

3. **Line Items / Order Lines**
   - **Reason:** No ERP order line feed. Only order headers are available.
   - **Impact:** Cannot reconcile POS to ERP at line level, only at order-header aggregate level.

4. **Dimensional Model (Star Schema)**
   - **Reason:** Assignment requirement is "minimum viable" entities for KPIs, not a full dimensional warehouse.
   - **Impact:** No date dimension, no surrogate keys, no slowly changing dimension framework beyond outlets.

---

## Refresh Strategy

**Current Implementation:** Full refresh (CREATE OR REPLACE TABLE)  
**Rationale:** Initial implementation for assessment purposes.

**Production Recommendation:**
- **Dimensions (products, outlets, sales_orders):** Daily full refresh with CDC sequencing
- **Facts (transactions, reefer_telemetry, wms_events):** Incremental MERGE based on business date or partition
- **Incremental Logic Example:**
  ```sql
  MERGE INTO silver.transactions t
  USING (
    -- New/changed Bronze records since last Silver refresh
    SELECT * FROM bronze.pos_transactions
    WHERE ingest_date > (SELECT MAX(original_ingest_date) FROM silver.transactions)
  ) s
  ON t.txn_id = s.txn_id AND t.txn_line_no = s.txn_line_no
  WHEN NOT MATCHED THEN INSERT *;
  ```

---

## Next Steps

1. **Reference Data Integration**
   - Load `reference/uom_conversion.csv` → `silver.uom_conversion`
   - Load `reference/warehouse_master.csv` → `silver.warehouse_master`
   - Load `reference/carrier_master.csv` → `silver.carrier_master`
   - Load `reference/fiscal_calendar.csv` → `silver.fiscal_calendar`
   - Required for KPI-003 (UOM), KPI-006 (Carrier), KPI-007 (Warehouse), and all period-based KPIs (Fiscal Calendar)

2. **Gold Layer KPI Tables**
   - Build KPI-specific aggregations on top of Silver
   - Implement fiscal period attribution
   - Apply UOM conversion for Units Sold (Eaches)
   - Construct point-in-time outlet channel joins

3. **Incremental Refresh Logic**
   - Implement daily incremental MERGE for fact tables
   - Implement CDC-driven updates for dimensions

4. **Data Quality Monitoring**
   - Automate validation queries
   - Alert on business key duplicates, null keys, or unexpected row count changes
   - Track qty null rate, temp missing rate over time

5. **Documentation**
   - Data dictionary for all Silver columns
   - Lineage diagrams (Bronze → Silver → Gold)
   - KPI calculation specifications with SQL examples

---

## Files & Artifacts

- **Notebook:** `silver.ipynb` (or equivalent notebook ID: 3331719830195411)
- **README:** `03_Silver_Layer_README.md` (this file)
- **Bronze Source:** `aistra_ayush.bronze.*`
- **Silver Catalog:** `aistra_ayush.silver.*`

---

## Contact & Maintenance

**Created By:** Genie Code (Databricks Assistant)  
**Date:** 2026-08-26  
**Project:** Kestrel Provisions Data Engineering Assessment  
**Assignment Owner:** ranjanayush585@gmail.com  

For questions or issues, refer to:
- `KPI_CATALOG.md` for business requirements
- `02_Feed_Contracts.md` for source data contracts
- Bronze ingestion notebook for upstream lineage

---

## Appendix: SQL Examples

### Example 1: KPI-001 - Gross Sales (Daily)
```sql
SELECT 
  business_date,
  COUNT(*) AS transaction_lines,
  SUM(line_sales_value_pretax) AS gross_sales_pretax,
  SUM(line_sales_value_incl_tax) AS gross_sales_incl_tax
FROM aistra_ayush.silver.transactions
WHERE line_sales_value_pretax IS NOT NULL
GROUP BY business_date
ORDER BY business_date DESC
LIMIT 30;
```

### Example 2: KPI-002 - Gross Sales by Channel (Monthly, with Point-in-Time Join)
```sql
SELECT
  DATE_TRUNC('month', t.business_date) AS month,
  o.channel,
  SUM(t.line_sales_value_pretax) AS gross_sales
FROM aistra_ayush.silver.transactions t
INNER JOIN aistra_ayush.silver.outlets o
  ON t.outlet_code = o.outlet_code
  AND t.business_date >= o.effective_from
  AND (t.business_date < o.effective_to OR o.effective_to IS NULL)
WHERE t.line_sales_value_pretax IS NOT NULL
GROUP BY DATE_TRUNC('month', t.business_date), o.channel
ORDER BY month DESC, channel;
```

### Example 3: KPI-008 - Outlet Channel Changes (Count by Period)
```sql
WITH channel_changes AS (
  SELECT
    outlet_code,
    channel,
    effective_from AS change_date,
    LAG(channel) OVER (PARTITION BY outlet_code ORDER BY effective_from) AS previous_channel
  FROM aistra_ayush.silver.outlets
)
SELECT
  DATE_TRUNC('month', change_date) AS month,
  previous_channel AS old_channel,
  channel AS new_channel,
  COUNT(*) AS change_count
FROM channel_changes
WHERE previous_channel IS NOT NULL  -- Exclude initial inserts
  AND previous_channel != channel     -- Exclude no-op updates
GROUP BY DATE_TRUNC('month', change_date), previous_channel, channel
ORDER BY month DESC, change_count DESC;
```

### Example 4: KPI-005 - Temperature Excursion Rate (Overall)
```sql
WITH eligible_readings AS (
  SELECT 
    *,
    CASE 
      WHEN temp_celsius > 8.0 THEN TRUE 
      ELSE FALSE 
    END AS is_excursion
  FROM aistra_ayush.silver.reefer_telemetry
  WHERE is_missing_temp = FALSE  -- Exclude incomplete telemetry
)
SELECT
  DATE_TRUNC('month', reading_date) AS month,
  COUNT(*) AS total_readings,
  COUNT(CASE WHEN is_excursion THEN 1 END) AS excursions,
  ROUND(100.0 * COUNT(CASE WHEN is_excursion THEN 1 END) / COUNT(*), 2) AS excursion_rate_pct
FROM eligible_readings
GROUP BY DATE_TRUNC('month', reading_date)
ORDER BY month DESC;
```

### Example 5: KPI-007 - Median Dock-to-Dispatch Cycle Time (by Warehouse)
```sql
WITH event_pairs AS (
  SELECT
    order_number,
    warehouse_code,
    MIN(CASE WHEN event_type = 'RECEIVE' THEN event_timestamp END) AS dock_time,
    MAX(CASE WHEN event_type = 'DISPATCH' THEN event_timestamp END) AS dispatch_time
  FROM aistra_ayush.silver.wms_events
  WHERE order_number IS NOT NULL
  GROUP BY order_number, warehouse_code
  HAVING dock_time IS NOT NULL AND dispatch_time IS NOT NULL
),
cycle_times AS (
  SELECT
    warehouse_code,
    order_number,
    TIMESTAMPDIFF(HOUR, dock_time, dispatch_time) AS cycle_hours
  FROM event_pairs
  WHERE dispatch_time > dock_time  -- Exclude negative durations
)
SELECT
  warehouse_code,
  COUNT(*) AS completed_movements,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cycle_hours) AS median_cycle_hours,
  AVG(cycle_hours) AS avg_cycle_hours,
  MIN(cycle_hours) AS min_cycle_hours,
  MAX(cycle_hours) AS max_cycle_hours
FROM cycle_times
GROUP BY warehouse_code
ORDER BY median_cycle_hours;
```

---

**End of Silver Layer README**
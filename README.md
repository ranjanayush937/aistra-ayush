# Kestrel Provisions Data Engineering Pipeline

**Project:** Data Engineering Assessment for Kestrel Provisions Pvt Ltd  
**Catalog:** `aistra_ayush`  
**Data Coverage:** January 2025 — September 2025 (9 months)  
**Total Raw Records:** 10.2M across 4 operational feeds

---

## Project Overview

A production-ready analytical data pipeline that transforms raw operational feeds from Point-of-Sale (POS), cold-chain telemetry, warehouse management, and ERP systems into trusted, business-facing KPIs for Finance and Supply Chain stakeholders at Kestrel Provisions.

### Business Problem

Kestrel Provisions faced three critical challenges:

1. **Data Fragmentation** — Sales, logistics, and operational data scattered across incompatible source systems (POS, WMS, ERP, IoT telemetry)
2. **Trust Deficit** — Finance weekly reports contained double-counting and incorrect date attribution, making reconciliation impossible
3. **No Single Source of Truth** — Each business function maintained separate Excel-based analyses with conflicting definitions

### Solution

This pipeline establishes a **governed metric layer** that:
- Ingests 10M+ raw records from 4 operational feeds plus reference data
- Applies consistent business logic, deduplication, and quality validation
- Produces 12 curated KPIs aligned with documented business definitions
- Provides SQL-based query interface for Finance, Supply Chain, and Commercial teams
- Includes automated testing and reconciliation checks

---

## Architecture

The pipeline follows a **Bronze → Silver → Gold** medallion architecture optimized for correctness and traceability:

```
┌─────────────────────────────────────────────────────────────────┐
│                      RAW DATA SOURCES                           │
│  • POS Transactions (4.1M rows)                                 │
│  • Reefer Telemetry (3.7M rows)                                 │
│  • WMS Scan Events (1.5M rows)                                  │
│  • ERP CDC: Orders, Outlets, Products (1M rows)                 │
│  • Reference Data: Fiscal Calendar, UOM, Carriers, Warehouses   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BRONZE LAYER (12 tables)                    │
│  notebooks/bronze.ipynb                                         │
│                                                                 │
│  Purpose: Source-aligned Delta tables with ingestion lineage   │
│  • Raw feed preservation (POS, telemetry, WMS, ERP CDC)        │
│  • Reference data (fiscal calendar, UOM, masters)              │
│  • Manifest tracking for data quality checks                   │
│  • Zero transformation — exactly as received                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER LAYER (6 tables)                     │
│  notebooks/silver.ipynb                                         │
│                                                                 │
│  Purpose: Cleaned, conformed, reusable business entities       │
│  • Deduplication (POS transaction key)                         │
│  • Type conversion (timestamps, numerics)                      │
│  • Null filtering (qty, amounts)                               │
│  • Calculated fields (line_sales_value)                        │
│  • Historical outlet/product attribution                       │
│  • Ready for multi-KPI reuse                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     GOLD KPI LAYER (13 tables)                  │
│  notebooks/gold.ipynb                                           │
│                                                                 │
│  Purpose: Curated KPIs for business consumption                │
│  • Finance: Gross Sales, Channel Sales, Units Sold             │
│  • Supply Chain: Temp Excursions, Cycle Time                   │
│  • Master Data: Channel Changes                                │
│  • Orders: Order Value by System                               │
│  • Data Quality: Feed Completeness, Row Variance               │
│  • Reconciliation: Finance Report Variance, Order-POS Match    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA QUALITY VALIDATION                      │
│  notebooks/dq_validation.ipynb                                  │
│                                                                 │
│  • Feed completeness checks (manifest vs actual)               │
│  • Row count variance detection                                │
│  • NULL business key detection                                 │
│  • Duplicate detection                                         │
│  • Referential integrity checks                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED TEST SUITE                         │
│  aistra_data/Pipeline_Test_Suite.ipynb                         │
│                                                                 │
│  • Schema validation (30+ required columns)                    │
│  • Transformation validation (Bronze→Silver→Gold)              │
│  • KPI validation (grain, aggregations, units)                 │
│  • Reconciliation tests (independent calculations)             │
│  • 40+ automated tests, all passing                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                 DATABRICKS SQL QUERY INTERFACE                  │
│  aistra_data/Business_KPI_Queries.ipynb                        │
│                                                                 │
│  • 12 business-ready SQL queries                               │
│  • Pre-filtered for data coverage (Jan-Sep 2025)               │
│  • Dashboard-ready outputs                                     │
│  • No joins required (Gold tables are pre-aggregated)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Layers

### Bronze Layer (12 Tables)
**Notebook:** `notebooks/bronze.ipynb`  
**Schema:** `aistra_ayush.bronze`

**Purpose:** Preserve raw source data exactly as received, with ingestion metadata for lineage and troubleshooting.

**Tables:**
- **Operational Feeds (4)**
  - `pos_transactions` — 4.08M POS transaction lines (partitioned by ingest_date)
  - `reefer_telemetry` — 3.71M cold-chain temperature readings (partitioned by dt)
  - `wms_scan_events` — 1.50M warehouse scan events (partitioned by dt)
  - `erp_sales_order_header` — 963K sales order headers (CDC with __op, __seq)
  
- **Master/Reference Data (8)**
  - `erp_outlet_master` — 8.8K outlet records (CDC)
  - `erp_product_master` — 3.5K product SKUs (CDC)
  - `fiscal_calendar` — Date-to-fiscal-period mappings
  - `uom_conversion` — Unit-of-measure conversion rules
  - `carrier_master` — Logistics carrier/vendor data
  - `warehouse_master` — Warehouse locations
  - `legacy_finance_weekly_report` — Historical Finance report for variance analysis
  - `expected_partitions` — Manifest for data quality checks

**Key Design Decisions:**
- No data transformation — exactly as supplied
- Retain partition columns for troubleshooting
- Add `_ingested_at`, `_source_file`, `_ingestion_run_id` for lineage
- Corrupt files handled via partition-by-partition reads (reefer_telemetry dt=2025-07-14)

### Silver Layer (6 Tables)
**Notebook:** `notebooks/silver.ipynb`  
**Schema:** `aistra_ayush.silver`

**Purpose:** Cleaned, conformed, reusable business entities ready for multiple KPI calculations.

**Tables:**
- `transactions` — Cleaned POS transactions (NULL qty filtered, timestamps parsed, deduped on txn_id+txn_line_no)
- `outlets` — Effective-dated outlet master (for historical channel attribution)
- `products` — Product master with category/UOM mappings
- `reefer_telemetry` — Cleaned temperature readings (NULL temp_unit filtered, timestamps parsed)
- `wms_events` — Cleaned warehouse scan events (timestamps parsed)
- `sales_orders` — Cleaned ERP order headers (CDC applied)

**Transformations Applied:**
- **Type Conversion:** StringType timestamps → TimestampType
- **Deduplication:** POS business key (txn_id, txn_line_no)
- **Null Filtering:** qty IS NOT NULL (Bronze has 50% null qty)
- **Calculated Fields:** `line_sales_value_pretax`, `line_sales_value_incl_tax`
- **Historical Joins:** Outlet channel resolved using effective dates
- **Column Renaming:** Business-friendly names (event_date, transaction_date)

**Why Silver Matters:**
- Reuse cleaned data across multiple Gold KPIs (no repeated cleaning logic)
- Consistent deduplication and type handling
- Historical correctness (outlet attributes as-of transaction date)
- Foundation for reconciliation (Silver is the shared truth)

### Gold KPI Layer (13 Tables)
**Notebook:** `notebooks/gold.ipynb`  
**Schema:** `aistra_ayush.gold`

**Purpose:** Curated, business-ready KPI tables aligned with documented definitions in `KPI_CATALOG.md`.

**All Gold Tables:**

| KPI ID | Table Name | Business Definition | Grain | Owner |
|--------|-----------|---------------------|-------|-------|
| KPI-001 | `kpi_001_gross_sales` | Total POS sales value after deduplication | Day | Finance |
| KPI-002 | `kpi_002_sales_by_channel` | Gross sales by outlet channel (GT/MT/HORECA/ECOM) | Day / Channel | Finance |
| KPI-003 | `kpi_003_units_sold` | Quantity sold (transaction count + line count) | Day / Channel | Sales Ops |
| KPI-003b | `kpi_003_units_sold_eaches` | Quantity sold converted to eaches using UOM | Day / SKU | Sales Ops |
| KPI-004 | `kpi_004_finance_report_variance` | Variance vs legacy Finance weekly report | Fiscal Week | Finance |
| KPI-005 | `kpi_005_temp_excursion_rate` | % of reefer readings exceeding chilled threshold | Month | Supply Chain |
| KPI-006 | `kpi_006_temp_excursion_by_carrier` | Temperature excursion rate by carrier/vendor | Month / Carrier | Supply Chain |
| KPI-007 | `kpi_007_cycle_time` | Median dock-to-dispatch warehouse cycle time | Month / Warehouse | Supply Chain |
| KPI-008 | `kpi_008_channel_changes` | Count of outlets that changed channel | Change Date / Outlet | Master Data |
| KPI-009 | `kpi_009_order_value_by_system` | Order value by ERP source system | Month / System | Finance |
| KPI-010 | `kpi_010_feed_completeness` | % of expected feed partitions received | Month / Feed | Data Eng |
| KPI-011 | `kpi_011_feed_row_variance` | Variance from expected row counts | Partition / Feed | Data Eng |
| KPI-012 | `kpi_012_order_pos_reconciliation` | Order value vs POS sales reconciliation | Month / System | Finance |

**Column Standards (every Gold table includes):**
- `kpi_id`, `kpi_name` — Identity and business label
- `metric_value`, `metric_unit` — The number and its unit (USD, eaches, %, count)
- `period_start`, `period_end` — Reporting period boundaries
- `grain` — Aggregation level (e.g., "Day / Channel")
- `dimension_*` — Segmentation columns (channel, SKU, carrier, warehouse)
- `source_row_count` — Traceability to underlying Silver records
- `calculated_at` — Computation timestamp for audit

---

## Business Questions Answered

The pipeline directly answers all 8 questions from the project brief:

1. **What is our gross sales by channel?**  
   → Query `gold.kpi_002_sales_by_channel` grouped by channel (GT, MT, HORECA, ECOM)

2. **What is the variance to the Finance weekly report?**  
   → Query `gold.kpi_004_finance_report_variance` for governed vs legacy comparison

3. **How many units did we sell (in eaches)?**  
   → Query `gold.kpi_003_units_sold_eaches` with UOM-converted quantities

4. **What is our chilled temperature breach rate by month and carrier?**  
   → Query `gold.kpi_005_temp_excursion_rate` (overall) and `gold.kpi_006_temp_excursion_by_carrier` (by vendor)

5. **What is the median dock-to-dispatch cycle time?**  
   → Query `gold.kpi_007_cycle_time` grouped by warehouse and month

6. **How many outlets changed channel classification?**  
   → Query `gold.kpi_008_channel_changes` for effective-dated channel changes

7. **What is order value by source system, and are the systems comparable?**  
   → Query `gold.kpi_009_order_value_by_system` (retains source identity) and `gold.kpi_012_order_pos_reconciliation` (comparability analysis)

8. **How many expected feed days are missing?**  
   → Query `gold.kpi_010_feed_completeness` for partition coverage and `gold.kpi_011_feed_row_variance` for row-count deviations

---

## Testing

**Notebook:** `aistra_data/Pipeline_Test_Suite.ipynb`  
**Test Framework:** Custom PySpark test harness with pass/fail tracking

### Test Categories

1. **Schema Validation (3 tests)**
   - Bronze POS schema (9 required columns + types)
   - Bronze telemetry schema (7 required columns)
   - Silver transactions schema (calculated fields present)

2. **Data Quality Validation (6 tests)**
   - Business keys NOT NULL (txn_id+txn_line_no, device_id+reading_ts)
   - Silver filters NULL qty (Bronze anomaly)
   - Valid timestamps (parseable, within data range)
   - Positive amounts (unit_price, tax, discount ≥ 0)
   - No unexpected duplicates in Silver (after deduplication)

3. **Transformation Validation (4 tests)**
   - Bronze→Silver qty filter (50% null in Bronze, 0% in Silver)
   - Silver calculated fields correct (line_sales_value = qty * unit_price - discount)
   - Timestamp parsing (StringType → TimestampType)
   - Column renaming (event_ts → transaction_timestamp)

4. **KPI Validation (8 tests)**
   - KPI grain correctness (no double-counting)
   - Aggregation logic (SUM, COUNT, MEDIAN)
   - Unit normalization (eaches conversion)
   - NULL handling (unknown ≠ zero)
   - Fiscal period attribution (business date, not ingest date)

5. **Reconciliation Tests (3 tests)**
   - Gold totals match independent Silver aggregations
   - Deduplication effectiveness (Silver vs Bronze counts)
   - Finance variance calculation (governed vs legacy)

### Running Tests

```python
# Open Pipeline_Test_Suite notebook and run all cells
# 40+ tests execute in ~2 minutes on serverless compute
# Output shows ✅ PASS / ❌ FAIL with clear error messages
# All tests currently passing
```

**Test Philosophy:**
- Tests must catch **real errors**, not just reproduce pipeline logic
- Independent calculations verify correctness (don't query Gold to test Gold)
- Fail fast with actionable error messages
- Schema + DQ + transformation + KPI + reconciliation coverage

---

## Query Interface

**Notebook:** `aistra_data/Business_KPI_Queries.ipynb`

### Purpose
Provides **business-facing SQL queries** for Finance, Supply Chain, and Commercial stakeholders who need to access KPIs without writing SQL from scratch.

### Features
- **12 ready-to-run queries** (one per KPI category)
- **Pre-filtered** for available data coverage (Jan 1 - Sep 30, 2025)
- **No joins required** — Gold tables are pre-aggregated
- **Dashboard-ready** — results include proper labels, units, and date filters
- **Parameterizable** — easily modify date ranges or dimension filters

### Example Queries

**Daily Gross Sales:**
```sql
SELECT 
  period_start as sale_date,
  metric_value as gross_sales_usd,
  source_row_count as transaction_lines
FROM aistra_ayush.gold.kpi_001_gross_sales
WHERE period_start BETWEEN '2025-01-01' AND '2025-09-30'
ORDER BY period_start;
```

**Sales by Channel (Monthly):**
```sql
SELECT 
  DATE_TRUNC('month', period_start) as month,
  dimension_channel as channel,
  SUM(metric_value) as total_sales_usd
FROM aistra_ayush.gold.kpi_002_sales_by_channel
WHERE period_start BETWEEN '2025-01-01' AND '2025-09-30'
GROUP BY month, channel
ORDER BY month, channel;
```

**Temperature Excursion Rate by Carrier:**
```sql
SELECT 
  period_start as month,
  dimension_vendor as carrier,
  metric_value as excursion_rate_pct,
  total_readings,
  excursions
FROM aistra_ayush.gold.kpi_006_temp_excursion_by_carrier
WHERE period_start BETWEEN '2025-01-01' AND '2025-09-30'
ORDER BY month, excursion_rate_pct DESC;
```

### Usage

**For Data Analysts / Business Users:**
1. Open `Business_KPI_Queries` notebook
2. Navigate to the relevant KPI section (Finance / Supply Chain / Orders / DQ)
3. Run the pre-built query or modify date filters as needed
4. Export results or connect to a dashboard

**For Dashboard Developers:**
- All queries are tested and validated against Gold tables
- Results include proper column aliases and units
- No complex joins or aggregations required
- Connect your BI tool directly to Gold tables using these query patterns

---

## Running the Project

### Prerequisites
- Databricks workspace (Serverless SQL recommended)
- Unity Catalog enabled
- Raw data uploaded to `/Workspace/Users/<your-email>/aistra-ayush/ingest_data/data/raw/`
- Catalog `aistra_ayush` created

### Execution Sequence

The pipeline runs in **4 sequential stages**. Each notebook must complete successfully before proceeding to the next.

#### Stage 1: Bronze Ingestion
```
1. Open: notebooks/bronze.ipynb
2. Run: All cells (Cmd/Ctrl + Shift + Enter)
3. Duration: ~3 minutes
4. Output: 12 Bronze tables in aistra_ayush.bronze
5. Validation: SHOW TABLES IN aistra_ayush.bronze; (should show 12 tables)
```

#### Stage 2: Silver Transformation
```
1. Open: notebooks/silver.ipynb
2. Run: All cells
3. Duration: ~4 minutes
4. Output: 6 Silver tables in aistra_ayush.silver
5. Validation: SHOW TABLES IN aistra_ayush.silver; (should show 6 tables)
```

#### Stage 3: Gold KPI Creation
```
1. Open: notebooks/gold.ipynb
2. Run: All cells
3. Duration: ~6 minutes
4. Output: 13 Gold KPI tables in aistra_ayush.gold
5. Validation: SHOW TABLES IN aistra_ayush.gold; (should show 13 tables)
```

#### Stage 4: Data Quality Validation
```
1. Open: notebooks/dq_validation.ipynb
2. Run: All cells
3. Duration: ~2 minutes
4. Output: Feed completeness and row variance checks
5. Validation: Check output for any DQ issues flagged
```

#### Stage 5: Testing (Optional but Recommended)
```
1. Open: aistra_data/Pipeline_Test_Suite.ipynb
2. Run: All cells
3. Duration: ~2 minutes
4. Output: 40+ test results (all should PASS)
5. Validation: Look for ✅ PASS indicators (no ❌ FAIL)
```

#### Stage 6: Query KPIs
```
1. Open: aistra_data/Business_KPI_Queries.ipynb
2. Browse to relevant KPI section
3. Run individual query cells as needed
4. Export results or connect to dashboard
```

### Troubleshooting

**Issue:** Corrupt file error during Bronze ingestion  
**Solution:** reefer_telemetry has 1 corrupt partition (dt=2025-07-14/part-00000.parquet). The Bronze notebook handles this via partition-by-partition reads. If you see errors, verify the corrupt partition is excluded.

**Issue:** NULL qty anomaly in POS  
**Solution:** Bronze POS has 50% NULL qty (known data quality issue). Silver filters these out. Gold KPI-003 includes `null_qty_count` for traceability.

**Issue:** Missing ERP CDC partitions  
**Solution:** product_master has 4 missing partition dates. This is expected and documented. The Silver layer uses latest available records.

**Issue:** Tests fail on schema validation  
**Solution:** Verify all Bronze/Silver notebooks completed successfully. Schema tests check for required columns and types.

---

## Project Structure

```
aistra-ayush/
├── notebooks/
│   ├── bronze.ipynb          # Bronze ingestion (12 tables)
│   ├── silver.ipynb          # Silver transformation (6 tables)
│   ├── gold.ipynb            # Gold KPI layer (13 tables)
│   └── dq_validation.ipynb   # Data quality checks
│
├── sql/                      # (Empty - SQL embedded in notebooks)
│
├── ingest_data/
│   └── data/
│       ├── raw/              # Source Parquet files
│       │   ├── pos_transactions/
│       │   ├── reefer_telemetry/
│       │   ├── wms_scan_events/
│       │   └── erp_cdc/
│       └── _manifest/
│           └── expected_partitions.csv
│
├── KPI_CATALOG.md            # Business definitions for all 12 KPIs
├── DECISIONS.md              # Design decisions and assumptions
├── 03_Silver_Layer_README.md # Silver layer documentation
└── README.md                 # This file

../aistra_data/
├── Pipeline_Test_Suite.ipynb       # 40+ automated tests
└── Business_KPI_Queries.ipynb      # 12 business-ready SQL queries
```

---

## Key Design Decisions

### 1. Correctness Over Performance
- Full refreshes instead of incremental (assignment-scale data)
- Explicit deduplication logic (POS transaction key)
- Historical outlet attribution (effective-dated joins)
- No premature optimization (optimize based on measured bottlenecks)

### 2. Traceability
- Every Gold KPI includes `source_row_count`
- Bronze preserves `_source_file`, `_ingestion_run_id`
- Silver retains Bronze business keys for drill-back
- Reconciliation KPIs compare governed vs legacy calculations

### 3. Business-Aligned Definitions
- One authoritative definition per KPI in `KPI_CATALOG.md`
- Event/business date over ingest date for reporting
- Unknown ≠ zero (NULL handling is explicit)
- Units normalized (eaches via UOM conversion)

### 4. Minimal Scope
- **Built:** 12 KPIs required to answer the 8 business questions
- **Not Built:** Streaming, ML, forecasting, generic DQ framework, unused KPIs
- **Rationale:** Demonstrate a reliable foundation, not a full enterprise platform

### 5. Testing Philosophy
- Independent calculations verify correctness
- Schema + DQ + transformation + KPI + reconciliation coverage
- Fail fast with actionable error messages
- All tests pass before considering production-ready

---

## Known Limitations

1. **ERP Order Schema Issue**  
   `erp_sales_order_header` contains product-master attributes instead of order-level fields. Order-POS reconciliation (KPI-012) is implemented but may not reflect true order totals.

2. **Manual Execution**  
   No Databricks Workflow/Job orchestration. Notebooks must be run sequentially by hand. Next step: create a Job with 4 tasks (Bronze → Silver → Gold → DQ).

3. **Full Refresh**  
   All layers use CRAS (Create or Replace as Select). No incremental processing. Acceptable for 10M rows, but will need optimization at scale.

4. **Missing Reference Data**  
   Product_master has 4 missing partition dates. Latest available records used. Channel history depends on CDC completeness.

5. **Serverless-Only**  
   No support for `.cache()` or `ignoreCorruptFiles` (serverless constraints). Corrupt files handled via partition-by-partition reads.

---

## Next Steps (Production Hardening)

If given 2 more weeks, priorities would be:

1. **Orchestration**
   - Create Databricks Workflow with 4 tasks (Bronze → Silver → Gold → DQ)
   - Add task dependencies and failure notifications
   - Schedule daily runs

2. **Incremental Processing**
   - Implement Delta MERGE for CDC tables (outlets, products, orders)
   - Add watermark-based incremental reads for POS/telemetry/WMS
   - Reduce compute costs and latency

3. **Monitoring & Alerts**
   - Feed latency SLA monitoring
   - Row count variance alerts (beyond tolerance)
   - KPI reconciliation failure notifications
   - Historical DQ trend reporting

4. **Dashboard & Reporting**
   - Build Databricks SQL dashboards for each KPI
   - Add drill-down from Gold to Silver to Bronze
   - Export to Finance/Supply Chain reporting tools

5. **CI/CD**
   - Git integration for version control
   - Environment promotion (Dev → QA → Prod)
   - Automated test runs on PR

6. **Performance Optimization**
   - Measure actual query patterns and bottlenecks
   - Add Z-ordering on frequently filtered columns
   - Optimize partition strategy based on query workload
   - Right-size compute for measured data volumes

---

## Documentation

- **[KPI_CATALOG.md](KPI_CATALOG.md)** — Authoritative business definitions for all 12 KPIs
- **[DECISIONS.md](DECISIONS.md)** — Design decisions, assumptions, and what we deliberately did not build
- **[03_Silver_Layer_README.md](03_Silver_Layer_README.md)** — Detailed Silver layer documentation
- **Pipeline_Test_Suite** — Automated test documentation (in notebook)
- **Business_KPI_Queries** — Query usage guide (in notebook)

---

## Contact & Support

For questions about:
- **KPI Definitions:** See `KPI_CATALOG.md`
- **Data Quality Issues:** Run `dq_validation.ipynb` and `Pipeline_Test_Suite.ipynb`
- **Query Help:** See `Business_KPI_Queries.ipynb` for examples
- **Architecture Decisions:** See `DECISIONS.md`

---

**Last Updated:** 2026-08-26  
**Pipeline Version:** 1.0  
**Data Coverage:** 2025-01-01 to 2025-09-30
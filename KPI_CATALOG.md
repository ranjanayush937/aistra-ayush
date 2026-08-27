# KPI Catalog

**Business:** Kestrel Provisions Pvt Ltd  
**Purpose:** Authoritative documentation for the KPI layer actually implemented in `gold.py`  
**Scope:** Assessment implementation only — documents the KPIs and calculations currently materialized in the Gold layer, including known implementation gaps and limitations.

## 1. KPI Design Principles

1. **One business definition:** each KPI has one documented calculation.
2. **Event/business date over ingest date:** reporting periods use the relevant business timestamp/date, not file arrival date.
3. **No silent double counting:** POS is calculated at transaction-line grain and deduplicated using the documented transaction key.
4. **Historical correctness:** outlet/channel attributes are evaluated using the effective-dated master record applicable to the transaction/event date.
5. **Units are normalized:** quantities are converted to eaches using the supplied UOM reference where conversion is available.
6. **Unknown is not zero:** missing or non-comparable source data is surfaced rather than converted to a zero value.
7. **Traceability:** every KPI can be traced from the gold result to the underlying source rows.

---

## 2. KPI Catalog

| KPI ID | KPI Name | Category | Business Definition | Grain | Filters / Exclusions | Source Feeds | Owner | Known Limitations |
|---|---|---|---|---|---|---|---|---|
| KPI-001 | Gross Sales | Finance / Sales | Daily sum of `line_sales_value_pretax` from POS transactions. | Day | Excludes NULL sales values. | `silver.transactions` | Finance | Current SQL does not deduplicate transaction keys before aggregation. |
| KPI-002 | Gross Sales by Channel | Finance / Sales | Daily POS sales grouped by outlet channel effective on the transaction business date. | Day / Channel | Point-in-time SCD2 join; excludes NULL sales values. | `silver.transactions` + `silver.outlets` | Finance | Inner join excludes transactions without a valid historical outlet match. |
| KPI-003 | Units Sold (Eaches) | Sales / Volume | Daily `SUM(qty)` by SKU, reported as EACHES under the current source-data assumption that `qty` is already in eaches. | Day / SKU | Inner join to product master. No UOM conversion is performed in current SQL. | `silver.transactions` + `silver.products` | Sales Operations | `case_pack` is not used; transaction UOM is unavailable in the current implementation. |
| KPI-004 | Finance Report Variance | Finance / Reconciliation | Variance between governed Gross Sales and the legacy Finance weekly report. | Fiscal week | Requires legacy Finance report data. | Governed POS KPI + legacy Finance report | Finance / Data | **Not implemented in `gold.py`.** |
| KPI-005 | Temperature Excursion Rate | Supply Chain / Cold Chain | Percentage of valid reefer telemetry readings above 8°C. | Month | Excludes `is_missing_temp = TRUE`. | `silver.reefer_telemetry` | Supply Chain Operations | Reading-level, not trip-level. Current SQL does not count <2°C as an excursion and does not deduplicate telemetry. |
| KPI-006 | Temperature Excursion Rate by Carrier | Supply Chain / Cold Chain | Percentage of valid telemetry readings above 8°C, grouped by `telemetry_vendor`. | Month / Vendor | Excludes missing temperature and NULL vendor. | `silver.reefer_telemetry` | Supply Chain Operations | `telemetry_vendor` is used as a proxy for carrier; confirm equivalence before labeling it Carrier. |
| KPI-007 | Median Dock-to-Dispatch Cycle Time | Supply Chain / Warehouse | Median elapsed hours from the first RECEIVE event to the last DISPATCH event per order/warehouse. | Month / Warehouse | Requires both events; excludes negative durations. | `silver.wms_events` | Supply Chain Operations | Current SQL uses whole-hour `TIMESTAMPDIFF` and first-RECEIVE/last-DISPATCH pairing. |
| KPI-008 | Outlet Channel Change Count | Master Data / Commercial | Number of outlets whose channel classification changed during the selected period, based on effective-dated outlet master history. | Outlet / change date / old channel / new channel | Count distinct effective changes; ignore unchanged CDC records. | ERP outlet master CDC; fiscal calendar | Commercial / Master Data | Requires reliable CDC sequencing and effective timestamps. Multiple changes within a period are counted as separate changes. |
| KPI-009 | Order Value by Source System | Order / Finance | Monthly sum of `order_value_gross` grouped by `source_system`. | Month / Source System | Excludes NULL order values. | `silver.sales_orders` | Finance / Order Management | Current SQL does not explicitly deduplicate order headers. |
| KPI-010 | Feed Data Completeness | Data Quality / Operations | Percentage of expected daily feed partitions with received data. | Month / Feed | Current template uses a hard-coded 2025-01-01 to 2026-06-30 expected range. | Intended: Bronze metadata + manifest | Data Engineering | **Template only:** `received_days` is currently hard-coded to 0. |
| KPI-011 | Feed Row-Count Variance | Data Quality / Operations | Difference between expected and observed feed row counts. | Feed / Partition | Requires manifest and Bronze metadata. | Manifest + Bronze metadata | Data Engineering | **Not implemented in `gold.py`.** |
| KPI-012 | Order-to-POS Value Reconciliation | Finance / Reconciliation | Monthly difference between total ERP order value and total POS sales value. | Month | Full outer join by month; missing side is currently converted to zero. | `silver.sales_orders` + `silver.transactions` | Finance | Diagnostic monthly comparison; does not prove comparable populations or transaction-level reconciliation. |

---

## 3. KPI Calculation Standards

### 3.1 Reporting Date

Use the business/event date associated with the metric:

- **POS:** transaction/business date.
- **Temperature:** trip/telemetry business date according to the trip definition.
- **WMS:** event timestamps for cycle-time calculations.
- **Outlet changes:** effective date of the master-data change.
- **Orders:** order business date.
- **Feed completeness:** expected partition/business date.

Ingest date is retained for lineage and operational monitoring but is not the default reporting date.

### 3.2 Deduplication

Deduplication must happen before aggregation.

For POS, the expected business key is:

`txn_id + txn_line_no`

For other feeds, the pipeline should use the documented source/business key and retain duplicate records as data-quality exceptions rather than silently aggregating them.

### 3.3 Null and Missing Data

- Missing numeric business values are **not automatically treated as zero**.
- Missing timestamps make a duration KPI unavailable for that event.
- Missing telemetry coverage is excluded from the excursion-rate denominator and reported as a coverage exception.
- Missing master-data mappings are surfaced as `UNKNOWN`/unmapped rather than guessed.

### 3.4 Fiscal Periods

All period-based KPIs should join to the supplied fiscal calendar. Queries should accept a date/fiscal-period parameter rather than hard-coding calendar periods.

---

## 4. Current Gold Tables

The current `gold.py` materializes these Gold tables:

1. `aistra_ayush.gold.kpi_001_gross_sales`
2. `aistra_ayush.gold.kpi_002_sales_by_channel`
3. `aistra_ayush.gold.kpi_003_units_sold_eaches`
4. `aistra_ayush.gold.kpi_005_temp_excursion_rate`
5. `aistra_ayush.gold.kpi_006_temp_excursion_by_carrier`
6. `aistra_ayush.gold.kpi_007_cycle_time`
7. `aistra_ayush.gold.kpi_008_channel_changes`
8. `aistra_ayush.gold.kpi_009_order_value_by_system`
9. `aistra_ayush.gold.kpi_012_order_pos_reconciliation`
10. `aistra_ayush.gold.kpi_010_feed_completeness` — template only

KPI-004 and KPI-011 are documented requirements but are not currently materialized by `gold.py`.

---

## 4. KPI Ownership

| Domain | Primary Owner | KPI IDs |
|---|---|---|
| Finance / Sales | Finance | KPI-001, KPI-002, KPI-004, KPI-009, KPI-012 |
| Commercial / Master Data | Commercial / Master Data | KPI-008 |
| Supply Chain | Supply Chain Operations | KPI-005, KPI-006, KPI-007 |
| Data Quality | Data Engineering | KPI-010, KPI-011 |
| Sales Operations | Sales Operations | KPI-003 |

---

## 5. Assessment Coverage

The catalog deliberately covers all eight example questions in the assignment:

1. **Gross sales by channel** → KPI-002
2. **Variance to Finance weekly report** → KPI-004
3. **Units sold in eaches** → KPI-003
4. **Chilled temperature breach rate by month/carrier** → KPI-005, KPI-006
5. **Median dock-to-dispatch cycle time** → KPI-007
6. **Outlet channel changes** → KPI-008
7. **Order value by source system/comparability** → KPI-009, KPI-012
8. **Missing feed days** → KPI-010, KPI-011

This is intentionally **not** a broad retail KPI library. Metrics such as gross margin, inventory turns, fill rate, OTIF, customer retention, forecast accuracy, and promotion ROI are excluded because the supplied assessment scope does not establish sufficient source data or business definitions to calculate them defensibly.

---

## 6. Recommended Gold KPI Output Columns

Every materialized KPI result should retain enough metadata to answer both “what is the number?” and “why is it this number?”:

- `kpi_id`
- `kpi_name`
- `metric_value`
- `metric_unit`
- `period_start`
- `period_end`
- `fiscal_period`
- `grain`
- `dimension_columns`
- `source_feeds`
- `source_row_count`
- `calculation_status`
- `data_quality_status`
- `definition_version`
- `calculated_at`

For reconciliation and audit use cases, retain the relevant source identifiers or a traceable lineage key so a KPI result can be followed back to source rows.

---

## 7. Implementation Priority

**P0 — Implemented / core**

- KPI-001 Gross Sales
- KPI-002 Gross Sales by Channel
- KPI-003 Units Sold (Eaches)
- KPI-005 Temperature Excursion Rate
- KPI-006 Temperature Excursion Rate by Carrier
- KPI-007 Median Dock-to-Dispatch Cycle Time
- KPI-008 Outlet Channel Change Count
- KPI-009 Order Value by Source System
- KPI-010 Feed Data Completeness

**P1 — Supporting / incomplete**

- KPI-011 Feed Row-Count Variance
- KPI-012 Order-to-POS Value Reconciliation

The current `gold.py` contains 10 Gold table definitions. KPI-004 and KPI-011 are not materialized, while KPI-010 is a template rather than a completed feed-completeness calculation.

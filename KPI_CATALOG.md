# KPI Catalog

**Business:** Kestrel Provisions Pvt Ltd  
**Purpose:** Single, documented metric layer for Finance and Supply Chain  
**Scope:** Assessment implementation only — intentionally limited to metrics that are directly supported by the supplied feeds/reference data and explicitly called for in the brief.

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
| KPI-001 | Gross Sales | Finance / Sales | Sum of eligible POS line sales value for the selected business period after transaction-level deduplication. | Transaction line / day / outlet / channel | Exclude invalid or duplicate transaction lines; use business transaction date; do not use ingest date for period attribution. | POS transactions; fiscal calendar; outlet master | Finance | POS represents partner sales, not necessarily total ERP order value. Returns/adjustments depend on source representation. |
| KPI-002 | Gross Sales by Channel | Finance / Sales | Gross Sales grouped by the outlet channel applicable on the transaction date. | Day / fiscal period / channel | Same exclusions as Gross Sales; resolve channel historically using effective-dated outlet master. | POS transactions; ERP outlet master; fiscal calendar | Finance | Channel history is dependent on correctness/completeness of ERP CDC history. |
| KPI-003 | Units Sold (Eaches) | Sales / Volume | Total quantity sold converted to eaches using the approved UOM conversion rules. | Transaction line / day / SKU / outlet | Exclude invalid/duplicate transaction lines; convert only with valid UOM mapping; unresolved conversions remain explicitly unconverted/flagged. | POS transactions; UOM reference | Sales Operations | Accuracy depends on UOM master coverage and the source quantity/UOM fields. |
| KPI-004 | Finance Report Variance | Finance / Reconciliation | Difference between the governed Gross Sales KPI and the published legacy Finance weekly report for the same reporting period. | Fiscal week | Compare only overlapping periods; do not alter governed sales to force agreement with the legacy report. | Governed POS KPI; legacy Finance weekly report; fiscal calendar | Finance / Data | Legacy report may contain double counting or incorrect date attribution, as stated in the brief. Variance is diagnostic, not a correction. |
| KPI-005 | Temperature Excursion Rate | Supply Chain / Cold Chain | Percentage of eligible reefer trips for which recorded telemetry breaches the applicable temperature threshold. | Trip / month / carrier | Eligible chilled/frozen trips only; exclude trips with insufficient telemetry from the denominator and report them separately as data-quality exceptions. | Reefer telemetry; carrier master; relevant trip/product classification | Supply Chain Operations | Threshold interpretation depends on the supplied telemetry/contract rules. Device-vendor differences may affect coverage and sampling. |
| KPI-006 | Temperature Excursion Rate by Carrier | Supply Chain / Cold Chain | Temperature Excursion Rate segmented by carrier to identify carrier-level cold-chain performance. | Month / carrier | Same eligibility and telemetry coverage rules as KPI-005. | Reefer telemetry; carrier master | Supply Chain Operations | Carrier attribution must be complete; missing/ambiguous carrier mappings reduce comparability. |
| KPI-007 | Median Dock-to-Dispatch Cycle Time | Supply Chain / Warehouse | Median elapsed time between the warehouse dock/receipt handling event and dispatch event for completed warehouse movements. | Warehouse / day or fiscal period | Include movements with valid start and end timestamps; exclude incomplete event sequences and negative durations. | WMS scan events; warehouse master | Supply Chain Operations | Requires a valid event sequence and timestamps. Incomplete scans are excluded rather than imputed. |
| KPI-008 | Outlet Channel Change Count | Master Data / Commercial | Number of outlets whose channel classification changed during the selected period, based on effective-dated outlet master history. | Outlet / change date / old channel / new channel | Count distinct effective changes; ignore unchanged CDC records. | ERP outlet master CDC; fiscal calendar | Commercial / Master Data | Requires reliable CDC sequencing and effective timestamps. Multiple changes within a period are counted as separate changes. |
| KPI-009 | Order Value by Source System | Order / Finance | Sum of order-header value by source system using the ERP order header business definition, without combining incompatible sources. | Order / source system / period | Exclude duplicate order headers; retain source-system identity; only compare systems where value definitions and currencies/units are compatible. | ERP sales order header CDC | Finance / Order Management | The three source systems may not be economically comparable; the catalog preserves source identity rather than assuming equivalence. |
| KPI-010 | Feed Data Completeness | Data Quality / Operations | Number and percentage of expected feed business dates/partitions that contain received data for the selected period. | Feed / business date | Compare observed dates against expected dates from the manifest/reference calendar; missing partitions are exceptions, not zero-valued business metrics. | Manifest; raw feed metadata; fiscal calendar | Data Engineering | Completeness indicates presence, not correctness of row content. A populated but corrupt partition can still appear complete. |
| KPI-011 | Feed Row-Count Variance | Data Quality / Operations | Difference between observed feed row counts and published expected row counts for each expected partition. | Feed / partition date | Flag material positive/negative variance according to the configured tolerance; retain actual and expected counts. | Manifest; raw feed metadata | Data Engineering | Expected counts come from the ingestion manifest and may themselves be wrong or stale. |
| KPI-012 | Order-to-POS Value Reconciliation | Finance / Reconciliation | Difference between governed order-header value and POS sales value for periods and dimensions where the source populations are explicitly comparable. | Period / source system / comparable business dimension | Do not force reconciliation across incompatible populations; show comparable and non-comparable populations separately. | ERP order headers; POS transactions; outlet master; fiscal calendar | Finance | POS and order-header feeds can represent different business events/populations. A non-zero difference is not automatically a data defect. |

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

**P0 — Must implement**

- KPI-001 Gross Sales
- KPI-002 Gross Sales by Channel
- KPI-003 Units Sold (Eaches)
- KPI-004 Finance Report Variance
- KPI-005 Temperature Excursion Rate
- KPI-006 Temperature Excursion Rate by Carrier
- KPI-007 Median Dock-to-Dispatch Cycle Time
- KPI-008 Outlet Channel Change Count
- KPI-009 Order Value by Source System
- KPI-010 Feed Data Completeness

**P1 — Strong supporting controls**

- KPI-011 Feed Row-Count Variance
- KPI-012 Order-to-POS Value Reconciliation

The P1 metrics strengthen the “one set of numbers” objective and make the system easier to defend, but they should not expand into a generic enterprise data-quality framework for this assessment.

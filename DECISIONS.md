# Decisions

## What we built

A minimal Databricks analytical foundation that runs end to end from the supplied raw feeds and produces trusted, business-facing KPIs.

The implementation consists of:

1. **Bronze** — source-aligned Delta tables preserving the supplied raw feeds and ingestion traceability.
2. **Silver** — cleaned and conformed data required to calculate the selected KPIs.
3. **Gold** — curated KPI outputs for business consumption.
4. **Data quality and reconciliation** — only checks that can materially affect KPI correctness.
5. **KPI catalogue** — one authoritative definition for every implemented metric.
6. **SQL query library** — runnable SQL behind the KPI catalogue.
7. **Databricks SQL output** — a usable interface for inspecting the resulting KPIs.

The pipeline is designed to run from raw data to business output using a documented command, without requiring notebook exploration or manual intervention.

## What we deliberately did not build

We deliberately did not build features that are not required to demonstrate a reliable analytical foundation:

- Machine learning or predictive modelling
- Forecasting
- Streaming/real-time processing
- A custom web application
- A large enterprise dimensional model
- A generic metadata/data-governance framework
- Advanced alerting
- Complex CI/CD infrastructure
- Unused KPIs or speculative business features
- Premature performance optimisation

The priority is correctness, traceability, reproducibility and usability.

## Issues

"erp_sales_order_header" cannot currently support sales-order reconciliation because its supplied schema contains product-master attributes rather than order-level fields.

## Assumptions and judgement calls

Where the brief or source feeds are ambiguous, the implementation uses the source data and feed contracts as the authority for available fields and relationships.

Business metrics are defined explicitly in the KPI catalogue rather than relying on implicit assumptions in SQL.

Where multiple feeds can represent the same business event, reconciliation is performed before the metric is considered trustworthy.

Where a required business concept cannot be reliably derived from the supplied feeds, it is documented as a limitation rather than inferred or fabricated.

The Gold layer contains only metrics that can be supported by the available data and have a clear business definition.

## What I would do with two more weeks

The next priority would be production hardening rather than adding more analytical features:

- Add automated pipeline testing and regression tests.
- Add stronger data-quality monitoring and historical DQ reporting.
- Add incremental processing and recovery mechanisms where required by volume.
- Improve dashboard usability and KPI drill-downs.
- Add CI/CD and environment promotion.
- Profile actual workloads and optimise storage/query performance based on measured bottlenecks.

## What breaks first in production

The first likely constraint is **data volume and ingestion/query latency**, rather than KPI logic.

The current design is intended for the supplied assignment-scale data and a single-machine/Databricks execution model. As data grows substantially, full refreshes and increasingly large joins/aggregations will become the first pressure points.

At that point, the first production changes should be incremental ingestion/processing, appropriate Delta optimisation and clustering, workload-aware compute sizing, and stronger pipeline observability.

The design deliberately avoids premature optimisation because the assignment provides a finite dataset and the correct production threshold should be determined from measured workload characteristics rather than an arbitrary volume assumption.
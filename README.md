# aistra-ayush

## Dataset Overview

**Scale:** 1.0

| Dataset                | Target Records |
| ---------------------- | -------------: |
| POS Transactions       |      4,000,000 |
| Reefer Telemetry       |      3,600,000 |
| WMS Scan Events        |      1,600,000 |
| Sales Orders           |        320,000 |

## Data Slices

### pos_transactions
```
slice 0: 500,000
slice 1: 500,000
slice 2: 500,000
slice 3: 500,000
slice 4: 500,000
slice 5: 500,000
slice 6: 500,000
slice 7: 500,000
```

### reefer_telemetry
```
slice 0: 500,000
slice 1: 500,000
slice 2: 500,000
slice 3: 500,000
slice 4: 500,000
slice 5: 500,000
slice 6: 500,000
slice 7: 100,000
```

### wms_scan_events
```
slice 0: 500,000
slice 1: 500,000
slice 2: 500,000
slice 3: 100,000
```

### erp_cdc/sales_order_header
```
slice 0: 320,000 orders
```

## Actual Row Counts

| Dataset                        |   Row Count |
| ------------------------------ | ----------: |
| pos_transactions               |   4,084,000 |
| reefer_telemetry               |   3,714,871 |
| wms_scan_events                |   1,496,000 |
| erp_cdc/sales_order_header     |     963,307 |
| erp_cdc/outlet_master          |       8,774 |
| erp_cdc/product_master         |       3,536 |
| **TOTAL**                      |  **10,270,488** |

## Notes

* **Reference data:** Available
* **Manifest:** Truncated at `data/raw/reefer_telemetry/dt=2025-07-14/part-00000.parquet`
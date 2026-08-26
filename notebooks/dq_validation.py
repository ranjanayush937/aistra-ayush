# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Setup and Imports
# =============================================================================
# SETUP AND CONFIGURATION
# =============================================================================

from pyspark.sql import functions as F
from datetime import datetime

# =============================================================================
# DQ BLOCKING THRESHOLD (Configurable)
# =============================================================================
# Failure percentage threshold above which a check status becomes BLOCK
# Below this threshold with failures: WARN
# At or above this threshold: BLOCK
DQ_BLOCK_THRESHOLD = 20.0  # Percentage (0-100)

# Generate single run timestamp for this DQ execution
run_timestamp = datetime.now()

print(f"DQ Validation Run Started: {run_timestamp}")
print(f"Target Catalog: aistra_ayush")
print(f"DQ Blocking Threshold: {DQ_BLOCK_THRESHOLD}%")
print(f"DQ Tables: aistra_ayush.dq.dq_results, aistra_ayush.dq.dq_failures")

# COMMAND ----------

# DBTITLE 1,Create DQ Schema and Tables
# =============================================================================
# CREATE DQ SCHEMA AND TABLES
# =============================================================================

# Create DQ schema if not exists
spark.sql("""
  CREATE SCHEMA IF NOT EXISTS aistra_ayush.dq
""")

# Create dq_results table
spark.sql("""
  CREATE TABLE IF NOT EXISTS aistra_ayush.dq.dq_results (
    check_name STRING,
    source_table STRING,
    check_type STRING,
    status STRING,
    failed_record_count BIGINT,
    checked_record_count BIGINT,
    run_timestamp TIMESTAMP
  )
  USING DELTA
""")

# Add severity and failure_percentage columns if they don't exist
try:
    spark.sql("""
      ALTER TABLE aistra_ayush.dq.dq_results 
      ADD COLUMNS (
        severity STRING,
        failure_percentage DOUBLE
      )
    """)
    print("Added severity and failure_percentage columns to dq_results.")
except Exception as e:
    if "already exists" in str(e).lower():
        print("Columns severity and failure_percentage already exist in dq_results.")
    else:
        raise

# Create dq_failures table
spark.sql("""
  CREATE TABLE IF NOT EXISTS aistra_ayush.dq.dq_failures (
    check_name STRING,
    source_table STRING,
    business_key STRING,
    failure_reason STRING,
    run_timestamp TIMESTAMP
  )
  USING DELTA
""")

print("DQ schema and tables ready.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - record_result
# =============================================================================
# GENERIC DQ FUNCTIONS
# =============================================================================

def record_result(
    check_name,
    source_table,
    check_type,
    failed_record_count,
    checked_record_count,
    run_timestamp,
    blocking_threshold=None
):
    """
    Record a DQ check result to dq_results table with severity calculation.
    
    Args:
        check_name: Name of the check
        source_table: Table being checked
        check_type: Type of check (required_fields, duplicates, invalid_values, referential_integrity, cross_feed_reconciliation)
        failed_record_count: Number of failed records
        checked_record_count: Total number of records checked
        run_timestamp: Timestamp of the run
        blocking_threshold: Optional blocking threshold percentage (defaults to DQ_BLOCK_THRESHOLD)
    """
    # Use global threshold if not specified
    if blocking_threshold is None:
        blocking_threshold = DQ_BLOCK_THRESHOLD
    
    # Calculate failure percentage
    if checked_record_count > 0:
        failure_percentage = (failed_record_count / checked_record_count) * 100.0
    else:
        failure_percentage = 0.0
    
    # Determine status and severity
    if failed_record_count == 0:
        status = "PASS"
        severity = "PASS"
    elif failure_percentage >= blocking_threshold:
        status = "BLOCK"
        severity = "BLOCK"
    else:
        status = "WARN"
        severity = "WARN"
    
    result_df = spark.createDataFrame([
        (check_name, source_table, check_type, status, failed_record_count, checked_record_count, run_timestamp, severity, failure_percentage)
    ], ["check_name", "source_table", "check_type", "status", "failed_record_count", "checked_record_count", "run_timestamp", "severity", "failure_percentage"])
    
    result_df.write.mode("append").saveAsTable("aistra_ayush.dq.dq_results")
    
print("Function record_result defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - record_failures
def record_failures(
    failures_df,
    check_name,
    source_table,
    business_key_columns,
    failure_reason,
    run_timestamp
):
    """
    Record failed business keys to dq_failures table.
    
    Args:
        failures_df: DataFrame containing failed records
        check_name: Name of the check
        source_table: Table being checked
        business_key_columns: List of column names forming the business key
        failure_reason: Reason for failure
        run_timestamp: Timestamp of the run
    """
    if failures_df.count() > 0:
        # Concatenate business key columns into single string
        business_key_expr = F.concat_ws(
            "|", 
            *[F.coalesce(F.col(c).cast("string"), F.lit("NULL")) for c in business_key_columns]
        )
        
        failures_to_record = failures_df.select(
            F.lit(check_name).alias("check_name"),
            F.lit(source_table).alias("source_table"),
            business_key_expr.alias("business_key"),
            F.lit(failure_reason).alias("failure_reason"),
            F.lit(run_timestamp).alias("run_timestamp")
        )
        
        failures_to_record.write.mode("append").saveAsTable("aistra_ayush.dq.dq_failures")

print("Function record_failures defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - check_required_fields
def check_required_fields(
    table_name,
    required_columns,
    business_key_columns,
    check_name
):
    """
    Check that required fields are not null.
    
    Args:
        table_name: Fully qualified table name
        required_columns: List of column names that must not be null
        business_key_columns: List of column names forming the business key
        check_name: Name of the check
        
    Returns:
        Dictionary with check results
    """
    df = spark.table(table_name)
    
    # Build condition: any required column is null
    null_condition = None
    for col in required_columns:
        if null_condition is None:
            null_condition = F.col(col).isNull()
        else:
            null_condition = null_condition | F.col(col).isNull()
    
    failures_df = df.filter(null_condition)
    failed_count = failures_df.count()
    checked_count = df.count()
    
    # Record result
    record_result(
        check_name=check_name,
        source_table=table_name,
        check_type="required_fields",
        failed_record_count=failed_count,
        checked_record_count=checked_count,
        run_timestamp=run_timestamp
    )
    
    # Record failures
    if failed_count > 0:
        record_failures(
            failures_df=failures_df,
            check_name=check_name,
            source_table=table_name,
            business_key_columns=business_key_columns,
            failure_reason="Required field(s) are null",
            run_timestamp=run_timestamp
        )
    
    # Calculate failure percentage for return
    failure_pct = (failed_count / checked_count * 100.0) if checked_count > 0 else 0.0
    
    # Determine status based on threshold
    if failed_count == 0:
        status = "PASS"
    elif failure_pct >= DQ_BLOCK_THRESHOLD:
        status = "BLOCK"
    else:
        status = "WARN"
    
    return {
        "check_name": check_name,
        "status": status,
        "failed_count": failed_count,
        "checked_count": checked_count,
        "failure_percentage": failure_pct
    }

print("Function check_required_fields defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - check_duplicates
def check_duplicates(
    table_name,
    business_key_columns,
    check_name
):
    """
    Check for duplicate records based on business key.
    
    Args:
        table_name: Fully qualified table name
        business_key_columns: List of column names forming the business key
        check_name: Name of the check
        
    Returns:
        Dictionary with check results
    """
    df = spark.table(table_name)
    
    # Find duplicates
    duplicates_df = df.groupBy(business_key_columns).agg(
        F.count("*").alias("row_count")
    ).filter(F.col("row_count") > 1)
    
    failed_count = duplicates_df.count()
    checked_count = df.count()
    
    # Record result
    record_result(
        check_name=check_name,
        source_table=table_name,
        check_type="duplicates",
        failed_record_count=failed_count,
        checked_record_count=checked_count,
        run_timestamp=run_timestamp
    )
    
    # Record failures
    if failed_count > 0:
        record_failures(
            failures_df=duplicates_df,
            check_name=check_name,
            source_table=table_name,
            business_key_columns=business_key_columns,
            failure_reason="Duplicate business key",
            run_timestamp=run_timestamp
        )
    
    # Calculate failure percentage for return
    failure_pct = (failed_count / checked_count * 100.0) if checked_count > 0 else 0.0
    
    # Determine status based on threshold
    if failed_count == 0:
        status = "PASS"
    elif failure_pct >= DQ_BLOCK_THRESHOLD:
        status = "BLOCK"
    else:
        status = "WARN"
    
    return {
        "check_name": check_name,
        "status": status,
        "failed_count": failed_count,
        "checked_count": checked_count,
        "failure_percentage": failure_pct
    }

print("Function check_duplicates defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - check_invalid_values
def check_invalid_values(
    table_name,
    invalid_condition,
    business_key_columns,
    check_name,
    failure_reason
):
    """
    Check for invalid values based on a condition.
    
    Args:
        table_name: Fully qualified table name
        invalid_condition: SQL condition string that identifies invalid records
        business_key_columns: List of column names forming the business key
        check_name: Name of the check
        failure_reason: Description of the failure
        
    Returns:
        Dictionary with check results
    """
    df = spark.table(table_name)
    
    failures_df = df.filter(invalid_condition)
    failed_count = failures_df.count()
    checked_count = df.count()
    
    # Record result
    record_result(
        check_name=check_name,
        source_table=table_name,
        check_type="invalid_values",
        failed_record_count=failed_count,
        checked_record_count=checked_count,
        run_timestamp=run_timestamp
    )
    
    # Record failures
    if failed_count > 0:
        record_failures(
            failures_df=failures_df,
            check_name=check_name,
            source_table=table_name,
            business_key_columns=business_key_columns,
            failure_reason=failure_reason,
            run_timestamp=run_timestamp
        )
    
    # Calculate failure percentage for return
    failure_pct = (failed_count / checked_count * 100.0) if checked_count > 0 else 0.0
    
    # Determine status based on threshold
    if failed_count == 0:
        status = "PASS"
    elif failure_pct >= DQ_BLOCK_THRESHOLD:
        status = "BLOCK"
    else:
        status = "WARN"
    
    return {
        "check_name": check_name,
        "status": status,
        "failed_count": failed_count,
        "checked_count": checked_count,
        "failure_percentage": failure_pct
    }

print("Function check_invalid_values defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - check_referential_integrity
def check_referential_integrity(
    child_table,
    parent_table,
    child_key,
    parent_key,
    business_key_columns,
    parent_filter,
    check_name
):
    """
    Check referential integrity between child and parent tables.
    
    Args:
        child_table: Fully qualified child table name
        parent_table: Fully qualified parent table name
        child_key: Column name in child table
        parent_key: Column name in parent table
        business_key_columns: List of column names forming the business key in child table
        parent_filter: SQL filter condition for parent table (e.g., "__op <> 'D'")
        check_name: Name of the check
        
    Returns:
        Dictionary with check results
    """
    child_df = spark.table(child_table).filter(F.col(child_key).isNotNull())
    parent_df = spark.table(parent_table)
    
    if parent_filter:
        parent_df = parent_df.filter(parent_filter)
    
    # Find child keys not in parent
    parent_keys = parent_df.select(F.col(parent_key)).distinct()
    
    failures_df = child_df.join(
        parent_keys,
        child_df[child_key] == parent_keys[parent_key],
        "left_anti"
    )
    
    failed_count = failures_df.count()
    checked_count = child_df.count()
    
    # Record result
    record_result(
        check_name=check_name,
        source_table=child_table,
        check_type="referential_integrity",
        failed_record_count=failed_count,
        checked_record_count=checked_count,
        run_timestamp=run_timestamp
    )
    
    # Record failures
    if failed_count > 0:
        record_failures(
            failures_df=failures_df,
            check_name=check_name,
            source_table=child_table,
            business_key_columns=business_key_columns,
            failure_reason=f"{child_key} not found in {parent_table}.{parent_key}",
            run_timestamp=run_timestamp
        )
    
    # Calculate failure percentage for return
    failure_pct = (failed_count / checked_count * 100.0) if checked_count > 0 else 0.0
    
    # Determine status based on threshold
    if failed_count == 0:
        status = "PASS"
    elif failure_pct >= DQ_BLOCK_THRESHOLD:
        status = "BLOCK"
    else:
        status = "WARN"
    
    return {
        "check_name": check_name,
        "status": status,
        "failed_count": failed_count,
        "checked_count": checked_count,
        "failure_percentage": failure_pct
    }

print("Function check_referential_integrity defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - check_cross_feed_reconciliation
def check_cross_feed_reconciliation(
    source_table,
    reference_table,
    source_key,
    reference_key,
    source_filter,
    reference_filter,
    check_name
):
    """
    Check cross-feed reconciliation (coverage check).
    
    Args:
        source_table: Fully qualified source table name
        reference_table: Fully qualified reference table name
        source_key: Column name in source table
        reference_key: Column name in reference table
        source_filter: SQL filter condition for source table
        reference_filter: SQL filter condition for reference table
        check_name: Name of the check
        
    Returns:
        Dictionary with check results
    """
    source_df = spark.table(source_table)
    if source_filter:
        source_df = source_df.filter(source_filter)
    
    reference_df = spark.table(reference_table)
    if reference_filter:
        reference_df = reference_df.filter(reference_filter)
    
    # Get distinct keys from both tables
    source_keys = source_df.select(F.col(source_key)).distinct()
    reference_keys = reference_df.select(F.col(reference_key)).distinct()
    
    # Find source keys not in reference
    missing_keys_df = source_keys.join(
        reference_keys,
        source_keys[source_key] == reference_keys[reference_key],
        "left_anti"
    )
    
    failed_count = missing_keys_df.count()
    checked_count = source_keys.count()
    
    # Record result
    record_result(
        check_name=check_name,
        source_table=source_table,
        check_type="cross_feed_reconciliation",
        failed_record_count=failed_count,
        checked_record_count=checked_count,
        run_timestamp=run_timestamp
    )
    
    # Record failures
    if failed_count > 0:
        record_failures(
            failures_df=missing_keys_df,
            check_name=check_name,
            source_table=source_table,
            business_key_columns=[source_key],
            failure_reason=f"{source_key} not found in {reference_table}.{reference_key}",
            run_timestamp=run_timestamp
        )
    
    # Calculate failure percentage for return
    failure_pct = (failed_count / checked_count * 100.0) if checked_count > 0 else 0.0
    
    # Determine status based on threshold
    if failed_count == 0:
        status = "PASS"
    elif failure_pct >= DQ_BLOCK_THRESHOLD:
        status = "BLOCK"
    else:
        status = "WARN"
    
    return {
        "check_name": check_name,
        "status": status,
        "failed_count": failed_count,
        "checked_count": checked_count,
        "failure_percentage": failure_pct
    }

print("Function check_cross_feed_reconciliation defined.")

# COMMAND ----------

# DBTITLE 1,Generic DQ Functions - get_valid_records
def get_valid_records(
    table_name,
    business_key_columns,
    check_names=None
):
    """
    Get valid records from a Bronze table by excluding failed business keys.
    
    Args:
        table_name: Fully qualified table name
        business_key_columns: List of column names forming the business key
        check_names: Optional list of specific check names to filter failures (if None, uses all checks)
        
    Returns:
        DataFrame containing only valid records (failed business keys excluded)
    """
    # Read the source table
    df = spark.table(table_name)
    
    # Read failures for this table
    failures = spark.table("aistra_ayush.dq.dq_failures").filter(
        (F.col("source_table") == table_name) &
        (F.col("run_timestamp") == run_timestamp)
    )
    
    # Filter by specific check names if provided
    if check_names:
        failures = failures.filter(F.col("check_name").isin(check_names))
    
    # If no failures, return all records
    if failures.count() == 0:
        return df
    
    # Create business key expression for both sides
    # The business_key in dq_failures is concatenated with "|"
    source_key_expr = F.concat_ws(
        "|",
        *[F.coalesce(F.col(c).cast("string"), F.lit("NULL")) for c in business_key_columns]
    )
    
    # Get distinct failed business keys
    failed_keys = failures.select(
        F.col("business_key")
    ).distinct()
    
    # Exclude failed records using LEFT ANTI JOIN
    valid_df = df.withColumn("_temp_business_key", source_key_expr)
    valid_df = valid_df.join(
        failed_keys,
        valid_df["_temp_business_key"] == failed_keys["business_key"],
        "left_anti"
    )
    
    return valid_df

print("Function get_valid_records defined.")

# COMMAND ----------

# DBTITLE 1,POS Checks
# =============================================================================
# POS CHECKS
# =============================================================================

results = []

print("\n=== POS TRANSACTION CHECKS ===")

# 1. Required fields
result = check_required_fields(
    table_name="aistra_ayush.bronze.pos_transactions",
    required_columns=["txn_id", "txn_line_no", "outlet_code", "sku_code", "event_ts", "unit_price"],
    business_key_columns=["txn_id", "txn_line_no"],
    check_name="pos_required_fields"
)
results.append(result)
print(f"pos_required_fields: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. Duplicates
result = check_duplicates(
    table_name="aistra_ayush.bronze.pos_transactions",
    business_key_columns=["txn_id", "txn_line_no"],
    check_name="pos_duplicates"
)
results.append(result)
print(f"pos_duplicates: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. Invalid values
result = check_invalid_values(
    table_name="aistra_ayush.bronze.pos_transactions",
    invalid_condition="""
        qty <= 0 
        OR unit_price < 0 
        OR discount_amount < 0 
        OR tax_amount < 0 
        OR try_cast(event_ts AS TIMESTAMP) IS NULL
    """,
    business_key_columns=["txn_id", "txn_line_no"],
    check_name="pos_invalid_values",
    failure_reason="Invalid qty/price/discount/tax or unparseable event_ts"
)
results.append(result)
print(f"pos_invalid_values: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,Reefer Telemetry Checks
# =============================================================================
# REEFER TELEMETRY CHECKS
# =============================================================================

print("\n=== REEFER TELEMETRY CHECKS ===")

# 1. Required fields
result = check_required_fields(
    table_name="aistra_ayush.bronze.reefer_telemetry",
    required_columns=["device_id", "vehicle_registration", "reading_ts", "temp_value", "temp_unit"],
    business_key_columns=["device_id", "reading_ts"],
    check_name="telemetry_required_fields"
)
results.append(result)
print(f"telemetry_required_fields: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. Duplicates
result = check_duplicates(
    table_name="aistra_ayush.bronze.reefer_telemetry",
    business_key_columns=["device_id", "reading_ts"],
    check_name="telemetry_duplicates"
)
results.append(result)
print(f"telemetry_duplicates: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. Invalid values
result = check_invalid_values(
    table_name="aistra_ayush.bronze.reefer_telemetry",
    invalid_condition="""
        try_cast(reading_ts AS TIMESTAMP) IS NULL
        OR temp_unit NOT IN ('C', 'F')
        OR humidity_pct < 0
        OR humidity_pct > 100
        OR battery_pct < 0
        OR battery_pct > 100
        OR door_open_flag NOT IN (0, 1)
    """,
    business_key_columns=["device_id", "reading_ts"],
    check_name="telemetry_invalid_values",
    failure_reason="Invalid reading_ts, temp_unit, humidity, battery, or door_open_flag"
)
results.append(result)
print(f"telemetry_invalid_values: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,WMS Scan Events Checks
# =============================================================================
# WMS SCAN EVENTS CHECKS
# =============================================================================

print("\n=== WMS SCAN EVENTS CHECKS ===")

# 1. Required fields
result = check_required_fields(
    table_name="aistra_ayush.bronze.wms_scan_events",
    required_columns=["scan_id", "warehouse_code", "event_type", "order_number", "sku_code", "event_ts"],
    business_key_columns=["scan_id"],
    check_name="wms_required_fields"
)
results.append(result)
print(f"wms_required_fields: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. Duplicates
result = check_duplicates(
    table_name="aistra_ayush.bronze.wms_scan_events",
    business_key_columns=["scan_id"],
    check_name="wms_duplicates"
)
results.append(result)
print(f"wms_duplicates: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. Invalid values
result = check_invalid_values(
    table_name="aistra_ayush.bronze.wms_scan_events",
    invalid_condition="""
        try_cast(event_ts AS TIMESTAMP) IS NULL
        OR qty_cases < 0
    """,
    business_key_columns=["scan_id"],
    check_name="wms_invalid_values",
    failure_reason="Invalid event_ts or negative qty_cases"
)
results.append(result)
print(f"wms_invalid_values: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,ERP Outlet Master Checks
# =============================================================================
# ERP OUTLET MASTER CHECKS
# =============================================================================

print("\n=== ERP OUTLET MASTER CHECKS ===")

# 1. Required fields
result = check_required_fields(
    table_name="aistra_ayush.bronze.erp_outlet_master",
    required_columns=["outlet_code", "__op", "__op_ts"],
    business_key_columns=["outlet_code", "__op_ts", "__seq"],
    check_name="erp_outlet_required_fields"
)
results.append(result)
print(f"erp_outlet_required_fields: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. CDC validity
result = check_invalid_values(
    table_name="aistra_ayush.bronze.erp_outlet_master",
    invalid_condition="""
        __op NOT IN ('I', 'U', 'D')
        OR try_cast(__op_ts AS TIMESTAMP) IS NULL
    """,
    business_key_columns=["outlet_code", "__op_ts", "__seq"],
    check_name="erp_outlet_cdc_validity",
    failure_reason="Invalid __op or unparseable __op_ts"
)
results.append(result)
print(f"erp_outlet_cdc_validity: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. Duplicate CDC sequence
result = check_duplicates(
    table_name="aistra_ayush.bronze.erp_outlet_master",
    business_key_columns=["outlet_code", "__op_ts", "__seq"],
    check_name="erp_outlet_duplicate_cdc_sequence"
)
results.append(result)
print(f"erp_outlet_duplicate_cdc_sequence: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,ERP Product Master Checks
# =============================================================================
# ERP PRODUCT MASTER CHECKS
# =============================================================================

print("\n=== ERP PRODUCT MASTER CHECKS ===")

# 1. Required fields
result = check_required_fields(
    table_name="aistra_ayush.bronze.erp_product_master",
    required_columns=["sku_code", "__op", "__op_ts"],
    business_key_columns=["sku_code", "__op_ts", "__seq"],
    check_name="erp_product_required_fields"
)
results.append(result)
print(f"erp_product_required_fields: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. Invalid values
result = check_invalid_values(
    table_name="aistra_ayush.bronze.erp_product_master",
    invalid_condition="""
        __op NOT IN ('I', 'U', 'D')
        OR try_cast(__op_ts AS TIMESTAMP) IS NULL
        OR mrp < 0
        OR list_price < 0
        OR gst_rate_pct < 0
        OR gst_rate_pct > 100
        OR case_pack < 0
        OR shelf_life_days < 0
        OR is_chilled NOT IN (0, 1)
    """,
    business_key_columns=["sku_code", "__op_ts", "__seq"],
    check_name="erp_product_invalid_values",
    failure_reason="Invalid __op, __op_ts, prices, gst_rate, case_pack, shelf_life, or is_chilled"
)
results.append(result)
print(f"erp_product_invalid_values: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. Duplicate CDC sequence
result = check_duplicates(
    table_name="aistra_ayush.bronze.erp_product_master",
    business_key_columns=["sku_code", "__op_ts", "__seq"],
    check_name="erp_product_duplicate_cdc_sequence"
)
results.append(result)
print(f"erp_product_duplicate_cdc_sequence: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,Referential Integrity Checks
# =============================================================================
# REFERENTIAL INTEGRITY CHECKS
# =============================================================================

print("\n=== REFERENTIAL INTEGRITY CHECKS ===")

# 1. POS outlet_code -> ERP outlet_code
result = check_referential_integrity(
    child_table="aistra_ayush.bronze.pos_transactions",
    parent_table="aistra_ayush.bronze.erp_outlet_master",
    child_key="outlet_code",
    parent_key="outlet_code",
    business_key_columns=["txn_id", "txn_line_no"],
    parent_filter="__op <> 'D'",
    check_name="pos_outlet_referential_integrity"
)
results.append(result)
print(f"pos_outlet_referential_integrity: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. POS sku_code -> ERP product sku_code
result = check_referential_integrity(
    child_table="aistra_ayush.bronze.pos_transactions",
    parent_table="aistra_ayush.bronze.erp_product_master",
    child_key="sku_code",
    parent_key="sku_code",
    business_key_columns=["txn_id", "txn_line_no"],
    parent_filter="__op <> 'D'",
    check_name="pos_sku_referential_integrity"
)
results.append(result)
print(f"pos_sku_referential_integrity: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. WMS sku_code -> ERP product sku_code
result = check_referential_integrity(
    child_table="aistra_ayush.bronze.wms_scan_events",
    parent_table="aistra_ayush.bronze.erp_product_master",
    child_key="sku_code",
    parent_key="sku_code",
    business_key_columns=["scan_id"],
    parent_filter="__op <> 'D'",
    check_name="wms_sku_referential_integrity"
)
results.append(result)
print(f"wms_sku_referential_integrity: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,Cross-Feed Reconciliation Checks
# =============================================================================
# CROSS-FEED RECONCILIATION CHECKS
# =============================================================================

print("\n=== CROSS-FEED RECONCILIATION CHECKS ===")

# 1. POS distinct outlet_code -> ERP outlet master
result = check_cross_feed_reconciliation(
    source_table="aistra_ayush.bronze.pos_transactions",
    reference_table="aistra_ayush.bronze.erp_outlet_master",
    source_key="outlet_code",
    reference_key="outlet_code",
    source_filter=None,
    reference_filter="__op <> 'D'",
    check_name="pos_outlet_cross_feed_coverage"
)
results.append(result)
print(f"pos_outlet_cross_feed_coverage: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 2. POS distinct sku_code -> ERP product master
result = check_cross_feed_reconciliation(
    source_table="aistra_ayush.bronze.pos_transactions",
    reference_table="aistra_ayush.bronze.erp_product_master",
    source_key="sku_code",
    reference_key="sku_code",
    source_filter=None,
    reference_filter="__op <> 'D'",
    check_name="pos_sku_cross_feed_coverage"
)
results.append(result)
print(f"pos_sku_cross_feed_coverage: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# 3. WMS distinct sku_code -> ERP product master
result = check_cross_feed_reconciliation(
    source_table="aistra_ayush.bronze.wms_scan_events",
    reference_table="aistra_ayush.bronze.erp_product_master",
    source_key="sku_code",
    reference_key="sku_code",
    source_filter=None,
    reference_filter="__op <> 'D'",
    check_name="wms_sku_cross_feed_coverage"
)
results.append(result)
print(f"wms_sku_cross_feed_coverage: {result['status']} ({result['failed_count']}/{result['checked_count']})")

# COMMAND ----------

# DBTITLE 1,DQ Summary
# =============================================================================
# DQ SUMMARY
# =============================================================================

print("\n" + "="*80)
print("DQ VALIDATION SUMMARY")
print("="*80)

# Create summary DataFrame from results list
summary_df = spark.createDataFrame(results)
print("\nAll Checks:")
display(summary_df.select("check_name", "status", "failed_count", "checked_count", "failure_percentage"))

# Show PASS checks
pass_checks_df = summary_df.filter(F.col("status") == "PASS")
if pass_checks_df.count() > 0:
    print("\n" + "="*80)
    print("✓ PASS CHECKS")
    print("="*80)
    display(pass_checks_df.select("check_name", "status", "checked_count"))

# Show WARN checks
warn_checks_df = summary_df.filter(F.col("status") == "WARN")
if warn_checks_df.count() > 0:
    print("\n" + "="*80)
    print("⚠ WARN CHECKS (Partial failures - below blocking threshold)")
    print("="*80)
    display(warn_checks_df.select("check_name", "status", "failed_count", "checked_count", "failure_percentage"))

# Show BLOCK checks
block_checks_df = summary_df.filter(F.col("status") == "BLOCK")
if block_checks_df.count() > 0:
    print("\n" + "="*80)
    print("✗ BLOCK CHECKS (Failures exceed blocking threshold)")
    print("="*80)
    display(block_checks_df.select("check_name", "status", "failed_count", "checked_count", "failure_percentage"))

# Show detailed failures
failures = spark.table("aistra_ayush.dq.dq_failures").filter(
    F.col("run_timestamp") == run_timestamp
)

if failures.count() > 0:
    print("\n" + "="*80)
    print("FAILED BUSINESS KEYS (Sample)")
    print("="*80)
    display(failures.limit(100))
    
    failure_count = failures.count()
    if failure_count > 100:
        print(f"\nShowing 100 of {failure_count} total failures. Query aistra_ayush.dq.dq_failures for complete list.")

# Calculate overall statistics
total_checks = len(results)
passed_checks = sum(1 for r in results if r['status'] == 'PASS')
warn_checks = sum(1 for r in results if r['status'] == 'WARN')
blocked_checks = sum(1 for r in results if r['status'] == 'BLOCK')

print("\n" + "="*80)
print("OVERALL STATISTICS")
print("="*80)
print(f"Total Checks Executed: {total_checks}")
print(f"Passed Checks: {passed_checks}")
print(f"Warning Checks: {warn_checks}")
print(f"Blocked Checks: {blocked_checks}")
print(f"Pass Rate: {(passed_checks/total_checks*100):.1f}%")

# COMMAND ----------

# DBTITLE 1,KPI Gate
# =============================================================================
# KPI GATE
# =============================================================================

# Determine overall DQ status
if blocked_checks > 0:
    overall_dq_status = "BLOCKED"
elif warn_checks > 0:
    overall_dq_status = "WARN"
else:
    overall_dq_status = "PASS"

print("\n" + "="*80)
print(f"DQ STATUS: {overall_dq_status}")
print("="*80)

if overall_dq_status == "PASS":
    print("✓ All DQ checks passed.")
    print("Downstream KPI processing can proceed with all data.")
    
elif overall_dq_status == "WARN":
    print(f"⚠ {warn_checks} check(s) returned WARN status.")
    print(f"Partial data quality issues detected, but below blocking threshold ({DQ_BLOCK_THRESHOLD}%).")
    print("\nDownstream KPI processing can proceed using VALID RECORDS.")
    print("\nInvalid records have been logged to aistra_ayush.dq.dq_failures.")
    print("Use get_valid_records() helper function to exclude failed business keys from downstream processing.")
    print("\nExample:")
    print("  valid_pos = get_valid_records('aistra_ayush.bronze.pos_transactions', ['txn_id', 'txn_line_no'])")
    
elif overall_dq_status == "BLOCKED":
    print(f"✗ {blocked_checks} check(s) returned BLOCK status.")
    print(f"Data quality failures exceed blocking threshold ({DQ_BLOCK_THRESHOLD}%).")
    print("Downstream KPI processing is BLOCKED until data quality issues are resolved.")
    print("\nReview failed checks above and investigate failures in aistra_ayush.dq.dq_failures table.")
    
    # Raise error to block downstream processing
    raise RuntimeError(
        f"DQ VALIDATION BLOCKED: {blocked_checks} of {total_checks} checks exceeded blocking threshold. "
        f"KPI processing cannot proceed until data quality issues are resolved. "
        f"Review aistra_ayush.dq.dq_results and aistra_ayush.dq.dq_failures for details."
    )

# COMMAND ----------

# DBTITLE 1,Example: Using get_valid_records()
# =============================================================================
# EXAMPLE: USING get_valid_records() FOR DOWNSTREAM PROCESSING
# =============================================================================

# This example demonstrates how to use get_valid_records() to exclude 
# failed business keys from downstream KPI processing when DQ status is WARN.

# Example 1: Get all valid POS records (excluding ALL failed checks)
print("\nExample 1: Get all valid POS records")
valid_pos = get_valid_records(
    table_name="aistra_ayush.bronze.pos_transactions",
    business_key_columns=["txn_id", "txn_line_no"]
)
print(f"Total POS records: {spark.table('aistra_ayush.bronze.pos_transactions').count()}")
print(f"Valid POS records: {valid_pos.count()}")

# Example 2: Get valid POS records excluding only specific checks
print("\nExample 2: Get valid POS records excluding only duplicate checks")
valid_pos_no_dupes = get_valid_records(
    table_name="aistra_ayush.bronze.pos_transactions",
    business_key_columns=["txn_id", "txn_line_no"],
    check_names=["pos_duplicates"]  # Only exclude records failed by this check
)
print(f"Valid POS records (excl. duplicates only): {valid_pos_no_dupes.count()}")

# Example 3: Get valid Telemetry records
print("\nExample 3: Get valid Telemetry records")
valid_telemetry = get_valid_records(
    table_name="aistra_ayush.bronze.reefer_telemetry",
    business_key_columns=["device_id", "reading_ts"]
)
print(f"Total Telemetry records: {spark.table('aistra_ayush.bronze.reefer_telemetry').count()}")
print(f"Valid Telemetry records: {valid_telemetry.count()}")

print("\n" + "="*80)
print("NOTE: Use get_valid_records() in downstream KPI calculations when DQ status is WARN.")
print("This ensures KPI calculations use only validated, quality-assured data.")
print("="*80)
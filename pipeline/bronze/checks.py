# Light validation
# pipeline/bronze/checks.py
import polars as pl
from pipeline.logging import logger


def light_schema_check(df: pl.DataFrame, expected_columns: list, source_name: str) -> bool:
    """Kiểm tra schema cơ bản"""
    actual_cols = df.columns
    missing = [col for col in expected_columns if col not in actual_cols]
    
    if missing:
        logger.warning("Schema validation failed - missing columns", 
                      source=source_name, missing_columns=missing)
        return False
    
    logger.info("Light schema check passed", source=source_name, row_count=len(df))
    return True


def check_required_fields(df: pl.DataFrame, key_columns: list, source_name: str) -> pl.DataFrame:
    """Kiểm tra null ở các cột khóa quan trọng"""
    null_counts = df.select([pl.col(col).is_null().sum().alias(f"{col}_null") for col in key_columns])
    
    for col in key_columns:
        null_count = null_counts[0, f"{col}_null"]
        if null_count > 0:
            logger.warning(f"Found null values in key column", column=col, null_count=int(null_count), source=source_name)
    
    return df


def run_bronze_checks(df: pl.DataFrame, source_name: str) -> bool:
    """Chạy tất cả light checks"""
    expected_sales = ["sale_id", "sale_date", "customer_id", "product_id", "quantity", "unit_price"]
    expected_customer = ["customer_id", "customer_name"]
    expected_product = ["product_id", "product_name"]
    
    if "sales" in source_name.lower():
        return light_schema_check(df, expected_sales, source_name)
    elif "customer" in source_name.lower():
        return light_schema_check(df, expected_customer, source_name)
    elif "product" in source_name.lower():
        return light_schema_check(df, expected_product, source_name)
    
    logger.warning("Unknown source schema, skipping file", source=source_name)
    return False

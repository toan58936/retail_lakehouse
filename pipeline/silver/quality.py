# Great Expectations
# pipeline/silver/quality.py
import polars as pl
from datetime import datetime

from pipeline.logging import logger

from .cleaner import get_silver_base_path, get_rejected_base_path


def validate_and_route(lf: pl.LazyFrame, entity_name: str, env_mode: str = "production") -> dict:
    """Validate dữ liệu và route valid / rejected"""
    
    # VÁ LỖI HIỆU NĂNG: Chỉ gọi collect() 1 lần duy nhất
    df = lf.collect()
    
    if df.height == 0:
        logger.warning("Empty dataset, skipping validation", entity=entity_name, env=env_mode)
        return {
            "entity": entity_name,
            "env_mode": env_mode,
            "rows_in": 0,
            "rows_valid": 0,
            "rows_rejected": 0,
            "valid_file": None,
            "rejected_file": None,
        }

    rows_in = df.height

    # Tạo rejected mask mặc định (Khởi tạo toàn bộ là False - tức là data sạch)
    rejected_mask = pl.lit(False)

    # Áp dụng luật kiểm định dựa trên Data Dictionary
    if entity_name == "customers":
        rejected_mask = (
            pl.col("customer_id").is_null() |
            pl.col("customer_name").is_null() |
            pl.col("email").is_null() |
            pl.col("region").is_null() |
            ~pl.col("region").is_in(["North", "South", "East", "West", "Central"])
        )
    elif entity_name == "products":
        rejected_mask = (
            pl.col("product_id").is_null() |
            pl.col("product_name").is_null() |
            pl.col("category").is_null() |
            (pl.col("unit_cost") <= 0)
        )
    elif entity_name == "sales":
        rejected_mask = (
            pl.col("sale_id").is_null() |
            pl.col("sale_date").is_null() |
            pl.col("customer_id").is_null() |
            pl.col("product_id").is_null() |
            pl.col("store_id").is_null() |
            (pl.col("quantity") < 1) |
            (pl.col("unit_price") <= 0)
        )

    # Tách dữ liệu thành 2 nhánh (Sạch và Lỗi)
    valid_df = df.filter(~rejected_mask)
    rejected_df = df.filter(rejected_mask)

    # Gắn metadata cho nhánh dữ liệu lỗi
    if rejected_df.height > 0:
        rejected_df = rejected_df.with_columns([
            pl.lit("Violated business rules or mandatory fields").alias("_reject_reason"),
            pl.lit(datetime.utcnow().isoformat()).alias("_rejected_at")
        ])

    # Thiết lập đường dẫn
    silver_base = get_silver_base_path(env_mode)
    rejected_base = get_rejected_base_path(env_mode)

    silver_base.mkdir(parents=True, exist_ok=True)
    rejected_base.mkdir(parents=True, exist_ok=True)

    # VÁ LỖI TÀNG HÌNH ĐUÔI FILE: Nối thêm ".parquet" vào tên file
    valid_file_path = silver_base / f"{entity_name}.parquet"
    rejected_file_path = rejected_base / f"{entity_name}.parquet"

# Ghi file (Polars mặc định sẽ ghi đè - đảm bảo tính Lũy đẳng)
    if valid_df.height > 0:
        valid_df.write_parquet(valid_file_path)
    if rejected_df.height > 0:
        rejected_df.write_parquet(rejected_file_path)

    # Logging chi tiết kết quả
    logger.info("Silver validation completed", 
               entity=entity_name,
               env=env_mode,
               rows_in=rows_in,
               rows_valid=valid_df.height,
               rows_rejected=rejected_df.height,
               reject_rate=round(rejected_df.height / rows_in * 100, 2) if rows_in > 0 else 0)

    return {
        "entity": entity_name,
        "env_mode": env_mode,
        "rows_in": rows_in,
        "rows_valid": valid_df.height,
        "rows_rejected": rejected_df.height,
        "valid_file": str(valid_file_path) if valid_df.height > 0 else None,
        "rejected_file": str(rejected_file_path) if rejected_df.height > 0 else None,
    }

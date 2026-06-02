# Silver Cleaning
# pipeline/silver/cleaner.py
import polars as pl
from pathlib import Path
from pipeline.config import settings
from pipeline.logging import logger


def _column_dtype(lf: pl.LazyFrame, column: str) -> pl.DataType | None:
    """Return a column dtype without collecting data rows."""
    return lf.collect_schema().get(column)


def _date_expr(lf: pl.LazyFrame, column: str) -> pl.Expr:
    """Normalize a column to Date whether Bronze stored it as string/date/datetime."""
    dtype = _column_dtype(lf, column)
    if dtype == pl.Date:
        return pl.col(column)
    if isinstance(dtype, pl.Datetime):
        return pl.col(column).dt.date()
    if dtype == pl.String:
        return pl.col(column).str.to_date(strict=False)
    return pl.col(column).cast(pl.Date, strict=False)


def _datetime_utc_expr(lf: pl.LazyFrame, column: str) -> pl.Expr:
    """Normalize a column to UTC Datetime without assuming it is a string."""
    dtype = _column_dtype(lf, column)
    if isinstance(dtype, pl.Datetime):
        if dtype.time_zone:
            return pl.col(column).dt.convert_time_zone("UTC")
        return pl.col(column).dt.replace_time_zone("UTC")
    if dtype == pl.String:
        return pl.col(column).str.to_datetime(strict=False).dt.replace_time_zone("UTC")
    return pl.col(column).cast(pl.Datetime, strict=False).dt.replace_time_zone("UTC")


def get_bronze_base_path(env_mode: str = "production") -> Path:
    """Lấy đường dẫn Bronze linh hoạt theo môi trường"""
    if env_mode == "sample":
        return Path(settings.STORAGE_ROOT) / "sample_env" / "bronze"
    return settings.get_layer_path("bronze")

def get_silver_base_path(env_mode: str = "production") -> Path:
    """Lấy đường dẫn Silver linh hoạt theo môi trường"""
    if env_mode == "sample":
        return Path(settings.STORAGE_ROOT) / "sample_env" / "silver"
    return settings.get_layer_path("silver")

def get_rejected_base_path(env_mode: str = "production") -> Path:
    """Lấy đường dẫn Silver Rejected linh hoạt theo môi trường"""
    if env_mode == "sample":
        return Path(settings.STORAGE_ROOT) / "sample_env" / "silver" / "silver_rejected"
    return settings.get_layer_path("rejected")

def _find_bronze_source_path(bronze_path: Path, entity_name: str) -> Path | None:
    """Find the Bronze folder for an entity, including older source-specific names."""
    exact_path = bronze_path / entity_name
    if exact_path.exists() and list(exact_path.rglob("*.parquet")):
        return exact_path

    if not bronze_path.exists():
        return None

    for candidate in sorted(bronze_path.iterdir()):
        if not candidate.is_dir():
            continue
        candidate_name = candidate.name.lower()
        if candidate_name.startswith(entity_name.lower()) and list(candidate.rglob("*.parquet")):
            return candidate

    return None

def clean_entity(entity_name: str, env_mode: str = "production") -> pl.LazyFrame:
    """Làm sạch dữ liệu theo Data Dictionary - Sử dụng LazyFrame"""
    logger.info("Starting cleaning", entity=entity_name, env=env_mode)

    bronze_path = get_bronze_base_path(env_mode)
    source_path = _find_bronze_source_path(bronze_path, entity_name)

    # LÁ CHẮN PHÒNG NGỰ: Kiểm tra xem thư mục có file Parquet nào không
    if source_path is None:
        logger.warning("No bronze data found or directory is empty", entity=entity_name, env=env_mode)
        return pl.LazyFrame()

    # Đọc an toàn toàn bộ file parquet (Bao gồm cả các sub-folder phân vùng của sales)
    lf = pl.scan_parquet(source_path / "**/*.parquet")

    if entity_name == "customers":
        lf = lf.with_columns([
            pl.col("customer_id").str.strip_chars().str.to_uppercase(),
            pl.col("customer_name").str.strip_chars().str.to_titlecase(),
            pl.col("email").str.strip_chars().str.to_lowercase(),
            pl.col("region").str.strip_chars().str.to_titlecase(),
            _datetime_utc_expr(lf, "created_at").alias("created_at"),
        ])

    elif entity_name == "products":
        lf = lf.with_columns([
            pl.col("product_id").str.strip_chars().str.to_uppercase(),
            pl.col("product_name").str.strip_chars(),
            pl.col("category").str.strip_chars().str.to_titlecase(),       # Đã vá lỗi
            pl.col("unit_cost").cast(pl.Float64).round(2)
        ])

    elif entity_name == "sales":
        lf = lf.with_columns([
            pl.col("sale_id").str.strip_chars().str.to_uppercase(),
            _date_expr(lf, "sale_date").alias("sale_date"),
            pl.col("customer_id").str.strip_chars().str.to_uppercase(),
            pl.col("product_id").str.strip_chars().str.to_uppercase(),
            pl.col("store_id").str.strip_chars().str.to_uppercase(),
            pl.col("quantity").cast(pl.Int32),
            pl.col("unit_price").cast(pl.Float64).round(2)
        ])

    # Deduplication (Bảo vệ tính lũy đẳng)
    if entity_name == "sales":
        lf = lf.unique(subset=["sale_id"], keep="first")
    else:
        # Tự động trích xuất customer_id hoặc product_id
        lf = lf.unique(subset=[f"{entity_name.rstrip('s')}_id"], keep="first")

    logger.info("Cleaning completed", entity=entity_name, env=env_mode)
    return lf

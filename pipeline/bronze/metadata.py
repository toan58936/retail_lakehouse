# Metadata injection
# pipeline/bronze/metadata.py
from datetime import datetime
import uuid
import polars as pl



def add_metadata(df: pl.DataFrame, source_file: str, load_id: str = None) -> pl.DataFrame:
    """Thêm metadata chuẩn cho Bronze Layer"""
    if load_id is None:
        load_id = f"LOAD_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    return df.with_columns([
        pl.lit(datetime.utcnow().isoformat()).alias("_ingested_at"),
        pl.lit(source_file).alias("_source_file"),
        pl.lit(load_id).alias("_load_id"),
        pl.lit("success").alias("_ingestion_status")
    ])


def generate_load_id() -> str:
    """Tạo Load ID unique"""
    return f"LOAD_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
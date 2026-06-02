# pipeline/bronze/ingestor.py
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

from pipeline.config import settings
from pipeline.logging import logger

from .checks import run_bronze_checks
from .metadata import add_metadata, generate_load_id


SAMPLE_MODE = "sample"
PRODUCTION_MODE = "production"
FULL_MODE = "full"
ALL_MODE = "all"


def normalize_env_mode(env_mode: str = PRODUCTION_MODE) -> str:
    """Normalize Bronze run mode while keeping old production/full aliases."""
    mode = env_mode.lower().strip()
    if mode == FULL_MODE:
        return PRODUCTION_MODE
    if mode in {SAMPLE_MODE, PRODUCTION_MODE, ALL_MODE}:
        return mode
    raise ValueError("env_mode must be one of: sample, full, production, all")


def get_bronze_base_path(env_mode: str = PRODUCTION_MODE) -> Path:
    """Return Bronze output root for sample or production data."""
    mode = normalize_env_mode(env_mode)
    base_storage = Path(settings.STORAGE_ROOT).resolve()

    if mode == SAMPLE_MODE:
        return base_storage / "sample_env" / "bronze"

    return settings.get_layer_path("bronze")


def _source_name(file_path: Path) -> str:
    source_name = file_path.stem.replace("_sample", "")
    source_key = source_name.lower()

    if "customer" in source_key:
        return "customers"
    if "product" in source_key:
        return "products"
    if "sales" in source_key:
        return "sales"

    return source_name


def _is_sample_file(file_path: Path) -> bool:
    return file_path.stem.endswith("_sample")


def _add_partition_columns(df: pl.DataFrame) -> pl.DataFrame:
    """Add year/month/day partitions from sale_date, or from ingestion date."""
    if "sale_date" in df.columns:
        df = df.with_columns(
            pl.col("sale_date")
            .str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            .alias("sale_date")
        )
        return df.with_columns([
            pl.col("sale_date").dt.year().alias("year"),
            pl.col("sale_date").dt.month().alias("month"),
            pl.col("sale_date").dt.day().alias("day"),
        ])

    ingest_date = datetime.now(timezone.utc).date()
    return df.with_columns([
        pl.lit(ingest_date.year).alias("year"),
        pl.lit(ingest_date.month).alias("month"),
        pl.lit(ingest_date.day).alias("day"),
    ])


def ingest_file(file_path: Path, env_mode: str = PRODUCTION_MODE) -> bool:
    """Ingest one CSV file into the Bronze layer."""
    try:
        mode = normalize_env_mode(env_mode)
        if mode == ALL_MODE:
            raise ValueError("ingest_file does not support env_mode='all'")

        logger.info("Starting ingestion", file=str(file_path), env=mode)
        start_time = datetime.now()

        df = pl.read_csv(file_path)
        source_name = _source_name(file_path)

        if not run_bronze_checks(df, source_name):
            logger.error("Schema check failed", file=str(file_path), source=source_name)
            return False

        load_id = generate_load_id()
        df = add_metadata(df, source_file=str(file_path), load_id=load_id)
        df = _add_partition_columns(df)

        output_path = get_bronze_base_path(mode) / source_name / load_id
        df.write_parquet(
            output_path,
            partition_by=["year", "month", "day"],
            mkdir=True,
        )

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(
            "Ingestion completed",
            source=source_name,
            rows=len(df),
            env=mode,
            output_path=str(output_path),
            load_id=load_id,
            duration_seconds=round(duration, 2),
        )
        return True
    except Exception as e:
        logger.error("Ingestion failed", file=str(file_path), error=str(e))
        return False


def _target_files(entity_path: Path, env_mode: str) -> list[Path]:
    all_csv_files = sorted(entity_path.glob("*.csv"))

    if env_mode == SAMPLE_MODE:
        return [file for file in all_csv_files if _is_sample_file(file)]

    return [file for file in all_csv_files if not _is_sample_file(file)]


def ingest_all_raw_data(env_mode: str = PRODUCTION_MODE) -> dict:
    """Ingest raw data according to sample/full/all mode."""
    mode = normalize_env_mode(env_mode)
    if mode == ALL_MODE:
        sample_summary = ingest_all_raw_data(SAMPLE_MODE)
        production_summary = ingest_all_raw_data(PRODUCTION_MODE)
        return {
            "env_mode": ALL_MODE,
            "total_files": sample_summary["total_files"] + production_summary["total_files"],
            "success_count": sample_summary["success_count"] + production_summary["success_count"],
            "success_rate": round(
                (
                    (sample_summary["success_count"] + production_summary["success_count"])
                    / (sample_summary["total_files"] + production_summary["total_files"])
                    * 100
                ),
                2,
            )
            if (sample_summary["total_files"] + production_summary["total_files"]) > 0
            else 0,
            "runs": [sample_summary, production_summary],
        }

    logger.info("Starting Bronze ingestion", env=mode)
    settings.ensure_directories()

    raw_path = Path(settings.STORAGE_ROOT) / "raw"
    bronze_base = get_bronze_base_path(mode)
    bronze_base.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total_files = 0

    for entity in ["customer", "product", "sales"]:
        entity_path = raw_path / entity
        if not entity_path.exists():
            logger.warning("Raw folder not found", entity=entity, path=str(entity_path))
            continue

        for file in _target_files(entity_path, mode):
            total_files += 1
            if ingest_file(file, mode):
                success_count += 1

    summary = {
        "env_mode": mode,
        "total_files": total_files,
        "success_count": success_count,
        "success_rate": round(success_count / total_files * 100, 2) if total_files else 0,
        "bronze_path": str(bronze_base),
    }
    logger.info("Bronze Ingestion finished", **summary)
    return summary


if __name__ == "__main__":
    ingest_all_raw_data(PRODUCTION_MODE)

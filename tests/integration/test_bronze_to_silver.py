from pathlib import Path

import polars as pl

from pipeline.bronze.ingestor import ingest_all_raw_data
from pipeline.config import settings
from pipeline.silver.cleaner import clean_entity
from pipeline.silver.quality import validate_and_route


def _write_sample_raw_data(storage_root: Path) -> None:
    customer_dir = storage_root / "raw" / "customer"
    product_dir = storage_root / "raw" / "product"
    sales_dir = storage_root / "raw" / "sales"

    customer_dir.mkdir(parents=True)
    product_dir.mkdir(parents=True)
    sales_dir.mkdir(parents=True)

    pl.DataFrame(
        {
            "customer_id": [" c001 ", "c002"],
            "customer_name": [" alice nguyen ", "bob tran"],
            "email": [" ALICE@EXAMPLE.COM ", "bob@example.com"],
            "region": [" north ", "south"],
            "created_at": ["2025-01-01T08:30:00", "2025-01-02T09:45:00"],
        }
    ).write_csv(customer_dir / "customers_sample.csv")

    pl.DataFrame(
        {
            "product_id": [" p001 ", "p002"],
            "product_name": [" Coffee Beans ", "Tea Box"],
            "category": [" grocery ", "beverage"],
            "unit_cost": [7.256, 3.5],
        }
    ).write_csv(product_dir / "products_sample.csv")

    pl.DataFrame(
        {
            "sale_id": [" s001 ", "s002"],
            "sale_date": ["2025-01-15", "2025-01-16"],
            "customer_id": [" c001 ", "c002"],
            "product_id": [" p001 ", "p002"],
            "store_id": [" store01 ", "store02"],
            "quantity": [2, 3],
            "unit_price": [12.5, 18.75],
        }
    ).write_csv(sales_dir / "sales_sample.csv")


def test_bronze_sample_outputs_feed_silver_sample(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    _write_sample_raw_data(tmp_path)

    bronze_summary = ingest_all_raw_data(env_mode="sample")

    assert bronze_summary["total_files"] == 3
    assert bronze_summary["success_count"] == 3

    bronze_root = tmp_path / "sample_env" / "bronze"
    assert list((bronze_root / "customers").rglob("*.parquet"))
    assert list((bronze_root / "products").rglob("*.parquet"))
    assert list((bronze_root / "sales").rglob("*.parquet"))

    for entity in ["customers", "products", "sales"]:
        cleaned_lf = clean_entity(entity, env_mode="sample")
        validate_and_route(cleaned_lf, entity, env_mode="sample")

    silver_root = tmp_path / "sample_env" / "silver"
    customers_df = pl.read_parquet(silver_root / "customers.parquet")
    products_df = pl.read_parquet(silver_root / "products.parquet")
    sales_df = pl.read_parquet(silver_root / "sales.parquet")

    assert customers_df.height == 2
    assert products_df.height == 2
    assert sales_df.height == 2

    assert sorted(customers_df["customer_id"].to_list()) == ["C001", "C002"]
    assert sorted(customers_df["region"].to_list()) == ["North", "South"]
    assert products_df.filter(pl.col("product_id") == "P001")["unit_cost"][0] == 7.26
    assert sales_df.schema["sale_date"] == pl.Date
    assert sorted(sales_df["store_id"].to_list()) == ["STORE01", "STORE02"]

    rejected_root = silver_root / "silver_rejected"
    assert not list(rejected_root.glob("*.parquet"))


def test_full_sales_file_name_feeds_silver_sales_entity(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))

    sales_dir = tmp_path / "raw" / "sales"
    sales_dir.mkdir(parents=True)
    pl.DataFrame(
        {
            "sale_id": ["s001"],
            "sale_date": ["2025-01-15"],
            "customer_id": ["c001"],
            "product_id": ["p001"],
            "store_id": ["store01"],
            "quantity": [2],
            "unit_price": [12.5],
        }
    ).write_csv(sales_dir / "sales_2025_2026.csv")

    bronze_summary = ingest_all_raw_data(env_mode="production")

    assert bronze_summary["total_files"] == 1
    assert bronze_summary["success_count"] == 1
    assert list((tmp_path / "bronze" / "sales").rglob("*.parquet"))

    cleaned_lf = clean_entity("sales", env_mode="production")
    silver_summary = validate_and_route(cleaned_lf, "sales", env_mode="production")

    assert silver_summary["rows_valid"] == 1
    sales_df = pl.read_parquet(tmp_path / "silver" / "sales.parquet")
    assert sales_df.height == 1
    assert sales_df["sale_id"][0] == "S001"

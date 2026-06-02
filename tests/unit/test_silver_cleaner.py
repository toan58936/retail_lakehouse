from pathlib import Path
from datetime import date

import polars as pl

from pipeline.config import settings
from pipeline.silver.cleaner import clean_entity


def test_clean_sales_accepts_bronze_date_dtype(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))

    bronze_sales_path = (
        Path(settings.STORAGE_ROOT)
        / "sample_env"
        / "bronze"
        / "sales"
        / "LOAD_TEST"
        / "year=2025"
        / "month=1"
        / "day=15"
    )
    bronze_sales_path.mkdir(parents=True)

    pl.DataFrame(
        {
            "sale_id": [" s001 "],
            "sale_date": [date(2025, 1, 15)],
            "customer_id": [" c001 "],
            "product_id": [" p001 "],
            "store_id": [" store01 "],
            "quantity": [2],
            "unit_price": [99.99],
        }
    ).write_parquet(bronze_sales_path / "part.parquet")

    df = clean_entity("sales", env_mode="sample").collect()

    assert df.height == 1
    assert df.schema["sale_date"] == pl.Date
    assert df["sale_id"][0] == "S001"

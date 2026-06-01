# tests/unit/test_bronze_ingestor.py
import polars as pl
import pytest
from pathlib import Path
from pipeline.bronze.ingestor import ingest_file, get_bronze_base_path
from pipeline.config import settings

@pytest.fixture
def sample_sales_df():
    return pl.DataFrame({
        "sale_id": ["S001", "S002"],
        "sale_date": ["2025-01-15", "2025-01-16"],
        "customer_id": ["C001", "C002"],
        "product_id": ["P001", "P002"],
        "store_id": ["STORE01", "STORE02"],
        "quantity": [2, 5],
        "unit_price": [99.99, 149.50]
    })


@pytest.fixture
def invalid_df():
    return pl.DataFrame({
        "sale_id": ["S001"],
        "wrong_column": ["value"]
    })


def test_ingest_file_success(tmp_path, monkeypatch, sample_sales_df):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    
    # Tạo file tạm
    temp_file = tmp_path / "temp_sales.csv"
    sample_sales_df.write_csv(temp_file)

    success = ingest_file(temp_file, env_mode="sample")
    assert success is True

    # Kiểm tra file Parquet đã được tạo
    bronze_path = get_bronze_base_path("sample")
    parquet_files = list(Path(bronze_path).rglob("*.parquet"))
    assert len(parquet_files) > 0


def test_ingest_file_schema_fail(tmp_path, monkeypatch, invalid_df):
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    
    temp_file = tmp_path / "invalid.csv"
    invalid_df.write_csv(temp_file)

    success = ingest_file(temp_file, env_mode="sample")
    assert success is False


def test_get_bronze_base_path():
    sample_path = get_bronze_base_path("sample")
    prod_path = get_bronze_base_path("production")
    
    assert "sample_env/bronze" in sample_path.as_posix()
    assert "data/bronze" in prod_path.as_posix()

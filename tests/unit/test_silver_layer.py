# tests/unit/test_silver_layer.py
import polars as pl
import pytest
from pathlib import Path
from pipeline.config import settings
from pipeline.silver.cleaner import clean_entity
from pipeline.silver.quality import validate_and_route

@pytest.fixture
def tmp_storage(monkeypatch, tmp_path):
    """Fixture ép toàn bộ STORAGE_ROOT vào thư mục tạm"""
    monkeypatch.setattr(settings, "STORAGE_ROOT", str(tmp_path))
    return tmp_path

@pytest.fixture
def mock_sales_dirty_df():
    """Mock data cho sales có lỗi cố ý để test cleaning"""
    return pl.DataFrame({
        "sale_id": [" SALE001 ", "SALE002", " SALE001 "],   # có khoảng trắng và duplicate
        "sale_date": ["2025-01-15", "2025-01-16", "2025-01-15"], # Đang là chuỗi String
        "customer_id": ["C001", "C002", "C001"],
        "product_id": ["P001", "P002", "P001"],
        "store_id": ["store01", "store02", "store01"],      # Đang là chữ thường
        "quantity": [5, 3, 5],
        "unit_price": [99.99, 149.50, 99.99]
    })

def test_clean_entity_sales(tmp_storage, mock_sales_dirty_df):
    """Test 1: clean_entity - Cleaning + Deduplication + Casting"""
    # Setup: Tạo file Parquet giả trong môi trường sample
    bronze_dir = tmp_storage / "sample_env" / "bronze" / "sales"
    bronze_dir.mkdir(parents=True, exist_ok=True)
    mock_sales_dirty_df.write_parquet(bronze_dir / "part-0.parquet")

    # Action
    lf = clean_entity("sales", env_mode="sample")
    result_df = lf.collect()

    # Assert 1: Deduplication
    assert len(result_df) == 2, "Phải còn lại 2 dòng sau deduplication"
    
    # Assert 2: Standardization (Kiểm tra đích danh giá trị)
    actual_sale_ids = sorted(result_df["sale_id"].to_list())
    assert actual_sale_ids == ["SALE001", "SALE002"], "sale_id phải được trim, viết hoa và xóa trùng lặp chuẩn xác"
    
    actual_store_ids = sorted(result_df["store_id"].to_list())
    assert actual_store_ids == ["STORE01", "STORE02"], "store_id phải được viết hoa toàn bộ"

    # Assert 3: Casting (Kiểm tra ép kiểu theo Data Dictionary)
    assert result_df["sale_date"].dtype == pl.Date, "sale_date phải được ép về kiểu pl.Date"
    assert result_df["quantity"].dtype == pl.Int32, "quantity phải được ép về kiểu pl.Int32"
    assert result_df["unit_price"].dtype == pl.Float64, "unit_price phải được ép về kiểu pl.Float64"

def test_validate_and_route_sales(tmp_storage):
    """Test 2: validate_and_route - Tách valid vs rejected"""
    # Setup: Tạo LazyFrame chứa cả valid và invalid records
    lf = pl.LazyFrame({
        "sale_id": ["SALE001", None, "SALE003", "SALE004"],
        "sale_date": ["2025-01-15", "2025-01-16", "2025-01-17", "2025-01-18"],
        "customer_id": ["C001", "C002", "C003", "C004"],
        "product_id": ["P001", "P002", "P003", "P004"],
        "store_id": ["STORE01", "STORE02", "STORE03", "STORE04"],
        "quantity": [5, 0, 3, 2],                  # Dòng 2 lỗi (quantity = 0)
        "unit_price": [99.99, 149.50, 0.0, 200.0]  # Dòng 3 lỗi (unit_price = 0)
    })

    # Action
    validate_and_route(lf, "sales", env_mode="sample")

    # VÁ LỖI TÌM FILE: Tìm chính xác file `sales.parquet`
    # Assert valid data
    valid_file = tmp_storage / "sample_env" / "silver" / "sales.parquet"
    assert valid_file.exists(), "Phải có file Parquet valid được tạo"

    valid_df = pl.read_parquet(valid_file)
    assert len(valid_df) == 2, "Chỉ được có 2 dòng valid (Dòng 1 và 4)"
    
    # Kiểm tra đích danh dòng nào lọt qua hải quan
    assert sorted(valid_df["sale_id"].to_list()) == ["SALE001", "SALE004"]

    # Assert rejected data
    rejected_file = tmp_storage / "sample_env" / "silver" / "silver_rejected" / "sales.parquet"
    assert rejected_file.exists(), "Phải có file rejected được tạo"

    rejected_df = pl.read_parquet(rejected_file)
    assert len(rejected_df) == 2, "Phải có đúng 2 dòng bị đẩy ra rejected (Dòng 2 và 3)"
    
    # Kiểm tra metadata của khu vực cách ly
    assert "_reject_reason" in rejected_df.columns, "Phải có cột _reject_reason"
    assert "_rejected_at" in rejected_df.columns, "Phải có cột _rejected_at"
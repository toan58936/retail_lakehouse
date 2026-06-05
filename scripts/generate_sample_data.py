# Report generator script
# scripts/generate_sample_data.py
"""
Retail Lakehouse - Synthetic Data Generator
Sinh dữ liệu bán lẻ thực tế cho demo Production
Sử dụng Faker + Polars để sinh dữ liệu chất lượng cao
"""

import polars as pl
from faker import Faker
from datetime import datetime, timedelta
import random
from pathlib import Path
import sys

# Ensure repo root is on sys.path when running as a script (e.g. in CI)
# Search for project root by looking for pipeline directory
script_dir = Path(__file__).resolve().parent
current = script_dir
while current != current.parent:
    if (current / "pipeline").is_dir():
        REPO_ROOT = current
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        break
    current = current.parent
else:
    # Fallback to parent[1] if pipeline not found
    REPO_ROOT = script_dir.parent
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

from pipeline.config import settings
from pipeline.logging import logger

fake = Faker()
Faker.seed(42)  # Để reproducible

def generate_customers(n: int = 10_000) -> pl.DataFrame:
    """Sinh dữ liệu khách hàng"""
    logger.info("Generating customers...", count=n)
    
    data = []
    for i in range(n):
        customer_id = f"CUST{10000 + i}"
        data.append({
            "customer_id": customer_id,
            "customer_name": fake.name(),
            "email": fake.email(),
            "region": random.choice(["North", "South", "East", "West", "Central"]),
            "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat()
        })
    
    return pl.DataFrame(data)


def generate_products(n: int = 1_000) -> pl.DataFrame:
    """Sinh dữ liệu sản phẩm"""
    logger.info("Generating products...", count=n)
    
    categories = ["Electronics", "Fashion", "Home", "Beauty", "Sports", "Food", "Books"]
    data = []
    
    for i in range(n):
        product_id = f"PROD{1000 + i}"
        category = random.choice(categories)
        data.append({
            "product_id": product_id,
            "product_name": fake.catch_phrase(),
            "category": category,
            "unit_cost": round(random.uniform(5.0, 500.0), 2)
        })
    
    return pl.DataFrame(data)


def generate_sales(
    n: int = 100_000,
    customers_df: pl.DataFrame = None,
    products_df: pl.DataFrame = None
) -> pl.DataFrame:
    """Sinh dữ liệu bán hàng"""
    logger.info("Generating sales transactions...", count=n)
    
    start_date = datetime(2025, 1, 1)
    
    data = []
    for i in range(n):
        sale_date = start_date + timedelta(days=random.randint(0, 450))
        customer_id = random.choice(customers_df["customer_id"].to_list())
        product_id = random.choice(products_df["product_id"].to_list())
        
        quantity = random.randint(1, 10)
        unit_price = round(random.uniform(10.0, 800.0), 2)
        
        data.append({
            "sale_id": f"SALE{100000 + i}",
            "sale_date": sale_date.strftime("%Y-%m-%d"),
            "customer_id": customer_id,
            "product_id": product_id,
            "store_id": f"STORE0{random.randint(1, 9)}",
            "quantity": quantity,
            "unit_price": unit_price
        })
    
    return pl.DataFrame(data)


def main():
    """Main function - Sinh toàn bộ dữ liệu"""
    logger.info("🚀 Starting Synthetic Data Generation")
    settings.ensure_directories()

    # Tạo thư mục raw nếu chưa có
    raw_path = Path("data/raw")
    raw_path.mkdir(parents=True, exist_ok=True)

    # Generate data
    customers = generate_customers(12_000)
    products = generate_products(1_200)
    sales = generate_sales(150_000, customers, products)

    # Lưu file CSV
    customers.write_csv("data/raw/customer/customers.csv")
    products.write_csv("data/raw/product/products.csv")
    sales.write_csv("data/raw/sales/sales_2025_2026.csv")

    logger.info("✅ Data generation completed successfully!")
    logger.info(f"   Customers : {len(customers):,} rows")
    logger.info(f"   Products  : {len(products):,} rows")
    logger.info(f"   Sales     : {len(sales):,} rows")


if __name__ == "__main__":
    main()
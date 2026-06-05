# scripts/generate_small_sample.py
"""
Retail Lakehouse - Small Sample Data Generator
Dùng cho Unit Test và Development nhanh
"""

import polars as pl
from faker import Faker
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
Faker.seed(123)

def generate_small_data():
    logger.info("Generating small sample dataset for testing...")

    settings.ensure_directories()

    # Customers
    customers = pl.DataFrame({
        "customer_id": [f"CUST{i:04d}" for i in range(1, 501)],
        "customer_name": [fake.name() for _ in range(500)],
        "email": [fake.email() for _ in range(500)],
        "region": random.choices(["North", "South", "East", "West"], k=500),
        "created_at": ["2024-01-01"] * 500
    })

    # Products
    products = pl.DataFrame({
        "product_id": [f"PROD{i:04d}" for i in range(1, 201)],
        "product_name": [fake.catch_phrase() for _ in range(200)],
        "category": random.choices(["Electronics", "Fashion", "Home", "Beauty"], k=200),
        "unit_cost": [round(random.uniform(10, 300), 2) for _ in range(200)]
    })

    # Sales
    sales = pl.DataFrame({
        "sale_id": [f"SALE{i:06d}" for i in range(1, 5001)],
        "sale_date": ["2025-01-15"] * 5000,
        "customer_id": random.choices(customers["customer_id"].to_list(), k=5000),
        "product_id": random.choices(products["product_id"].to_list(), k=5000),
        "store_id": [f"STORE0{random.randint(1,5)}" for _ in range(5000)],
        "quantity": random.choices(range(1, 11), k=5000),
        "unit_price": [round(random.uniform(15, 450), 2) for _ in range(5000)]
    })

    # Save to CSV
    customers.write_csv("data/raw/customer/customers_sample.csv")
    products.write_csv("data/raw/product/products_sample.csv")
    sales.write_csv("data/raw/sales/sales_sample.csv")

    logger.info("✅ Small sample data generated successfully!")
    logger.info(f"   Customers: {len(customers)} rows")
    logger.info(f"   Products : {len(products)} rows")
    logger.info(f"   Sales    : {len(sales)} rows")

    # Generate silver layer parquet for dbt snapshots
    logger.info("Generating silver layer parquet files for dbt snapshots...")
    silver_path = Path("data/silver")
    silver_path.mkdir(parents=True, exist_ok=True)
    
    # Apply silver layer cleaning transformations
    customers_silver = customers.with_columns([
        pl.col("customer_id").str.strip_chars().str.to_uppercase(),
        pl.col("customer_name").str.strip_chars().str.to_titlecase(),
        pl.col("email").str.strip_chars().str.to_lowercase(),
        pl.col("region").str.strip_chars().str.to_titlecase(),
    ])
    
    products_silver = products.with_columns([
        pl.col("product_id").str.strip_chars().str.to_uppercase(),
        pl.col("product_name").str.strip_chars(),
        pl.col("category").str.strip_chars().str.to_titlecase(),
        pl.col("unit_cost").cast(pl.Float64).round(2)
    ])
    
    sales_silver = sales.with_columns([
        pl.col("sale_id").str.strip_chars().str.to_uppercase(),
        pl.col("customer_id").str.strip_chars().str.to_uppercase(),
        pl.col("product_id").str.strip_chars().str.to_uppercase(),
        pl.col("store_id").str.strip_chars().str.to_uppercase(),
        pl.col("quantity").cast(pl.Int32),
        pl.col("unit_price").cast(pl.Float64).round(2)
    ]).unique(subset=["sale_id"], keep="first")
    
    # Write to parquet
    customers_silver.write_parquet(silver_path / "customers.parquet")
    products_silver.write_parquet(silver_path / "products.parquet")
    sales_silver.write_parquet(silver_path / "sales.parquet")
    
    logger.info("✅ Silver layer parquet files created for dbt snapshots!")


if __name__ == "__main__":
    generate_small_data()
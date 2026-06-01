# scripts/generate_small_sample.py
"""
Retail Lakehouse - Small Sample Data Generator
Dùng cho Unit Test và Development nhanh
"""

import polars as pl
from faker import Faker
import random
from pathlib import Path
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

    # Save
    customers.write_csv("data/raw/customer/customers_sample.csv")
    products.write_csv("data/raw/product/products_sample.csv")
    sales.write_csv("data/raw/sales/sales_sample.csv")

    logger.info("✅ Small sample data generated successfully!")
    logger.info(f"   Customers: {len(customers)} rows")
    logger.info(f"   Products : {len(products)} rows")
    logger.info(f"   Sales    : {len(sales)} rows")


if __name__ == "__main__":
    generate_small_data()
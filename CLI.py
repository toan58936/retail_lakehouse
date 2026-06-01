#!/usr/bin/env python
# cli.py - Command Line Interface cho Retail Lakehouse
import typer
from typing import Optional
from pipeline.config import settings
from pipeline.logging import logger

app = typer.Typer(
    name="retail-lakehouse",
    help="Retail Sales Modern Data Lakehouse CLI Tool",
    add_completion=True
)

@app.command()
def init():
    """Khởi tạo thư mục và config"""
    settings.ensure_directories()
    typer.echo("✅ Project initialized successfully!")
    typer.echo(f"Environment : {settings.ENV}")
    typer.echo(f"Storage root: {settings.STORAGE_ROOT}")

@app.command()
def ingest():
    """Chạy Bronze Ingestion"""
    typer.echo("🚀 Starting Bronze Ingestion...")
    # Sẽ import và chạy sau khi implement Bronze
    logger.info("Bronze ingestion started via CLI")

@app.command()
def transform():
    """Chạy Silver Transformation"""
    typer.echo("🧹 Starting Silver Cleaning & Standardization...")

@app.command()
def build():
    """Chạy Gold Layer"""
    typer.echo("🏗️  Building Gold Layer (Dimensional Modeling)...")

@app.command()
def run():
    """Chạy toàn bộ pipeline"""
    typer.echo("⚡ Running full pipeline...")
    # Import orchestrator sau

@app.command()
def status():
    """Hiển thị thông tin config hiện tại"""
    typer.echo("📊 Project Status:")
    typer.echo(f"   ENV            : {settings.ENV}")
    typer.echo(f"   STORAGE_ROOT   : {settings.STORAGE_ROOT}")
    typer.echo(f"   BATCH_SIZE     : {settings.BATCH_SIZE}")
    typer.echo(f"   LOG_FILE       : {settings.LOG_FILE}")

if __name__ == "__main__":
    app()
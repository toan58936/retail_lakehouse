# Makefile - Dành cho Linux, CI/CD, Production

.PHONY: install sync clean help run-all test lint docker-build dbt-snapshot dbt-run dbt-test

install:  ## Cài đặt môi trường uv và dependencies
	uv python install 3.11
	uv sync

sync:  ## Sync dependencies nhanh
	uv sync

clean:  ## Dọn dẹp cache
	rm -rf .venv uv.lock __pycache__ .pytest_cache reports/ logs/ data/gold/lakehouse.duckdb data/sample_env/gold/lakehouse.duckdb


# Pipeline Commands
ingest-bronze:  ## Chạy Bronze Layer
	uv run python -m pipeline.bronze.ingestor

transform-silver:  ## Chạy Silver Layer
	uv run python -m pipeline.silver.cleaner

build-gold:  ## Chạy Gold Layer
	uv run python -m pipeline.gold.fact_sales

run-all:  ## Chạy toàn bộ pipeline
	uv run python -m pipeline.orchestrator

# Development & Quality
test:  ## Chạy tests
	uv run pytest tests/

lint:  ## Kiểm tra code style
	uv run ruff check pipeline/

dbt-snapshot:  ## Chạy dbt snapshots
	cd dbt && uv run dbt snapshot --select snp_*

dbt-run:  ## Chạy dbt models (marts)
	cd dbt && uv run dbt run --select +marts

dbt-test:  ## Chạy dbt tests cho marts
	cd dbt && uv run dbt test --select marts



reports:  ## Tạo reports
	uv run python scripts/generate_reports.py

# Makefile (Trích đoạn phần cuối)
# Docker
docker-build:  ## Build Docker image
	docker compose build

docker-run-sample:  ## Chạy pipeline môi trường Sample trong Docker
	docker compose --profile sample up

docker-run-prod:  ## Chạy pipeline môi trường Prod trong Docker
	docker compose --profile prod up
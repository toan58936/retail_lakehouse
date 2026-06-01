# Makefile - Dành cho Linux, CI/CD, Production

.PHONY: install sync clean help run-all test lint docker-build

install:  ## Cài đặt môi trường uv và dependencies
	uv python install 3.11
	uv sync

sync:  ## Sync dependencies nhanh
	uv sync

clean:  ## Dọn dẹp cache
	rm -rf .venv uv.lock __pycache__ .pytest_cache reports/ logs/

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

dbt-run:  ## Chạy dbt models
	cd dbt && uv run dbt run

reports:  ## Tạo reports
	uv run python scripts/generate_reports.py

# Docker
docker-build:  ## Build Docker image
	docker build -t retail-lakehouse:latest .

docker-run:  ## Chạy pipeline trong Docker
	docker run --rm -v $(PWD)/data:/app/data retail-lakehouse:latest make run-all

help:  ## Hiển thị danh sách lệnh
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
# ============================================================
#  Retail Sales Modern Data Lakehouse — FULL PRODUCTION SETUP
#  Version: 0.2.0 (uv + 2-Layer Config + Production Grade)
#  Chạy: .\setup_retail_lakehouse_full.ps1
# ============================================================

param(
    [string]$Root = ".\retail_lakehouse"
)

function New-Dir { 
    param([string]$Path)
    New-Item -ItemType Directory -Path $Path -Force | Out-Null
}

function New-File { 
    param([string]$Path, [string]$Content = "")
    $dir = Split-Path $Path
    if ($dir) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    New-Item -ItemType File -Path $Path -Force | Out-Null
    if ($Content) { 
        Set-Content -Path $Path -Value $Content -Encoding UTF8 
    }
}

Write-Host ""
Write-Host "  Retail Lakehouse — Tạo cấu trúc Production Full (uv + Config v2)..." -ForegroundColor Cyan
Write-Host "  Root: $Root" -ForegroundColor DarkGray
Write-Host ""

# ── Root Files ────────────────────────────────────────────────
New-File "$Root\README.md" "# Retail Sales Modern Data Lakehouse`n`nProduction-grade Medallion Architecture với uv + 2-Layer Config"

New-File "$Root\Makefile" @"
.PHONY: install sync clean run-all test lint docker-build

install:  ## Cài đặt môi trường uv
	uv python install 3.11
	uv sync

sync:  ## Sync dependencies
	uv sync

clean:
	rm -rf .venv uv.lock __pycache__ .pytest_cache

# Pipeline
ingest-bronze:
	uv run python -m pipeline.bronze.ingestor

transform-silver:
	uv run python -m pipeline.silver.cleaner

build-gold:
	uv run python -m pipeline.gold.fact_sales

run-all:
	uv run python -m pipeline.orchestrator

# Utils
test:
	uv run pytest tests/

lint:
	uv run ruff check pipeline/

dbt-run:
	cd dbt && uv run dbt run

reports:
	uv run python scripts/generate_reports.py

docker-build:
	docker build -t retail-lakehouse:latest .

docker-run:
	docker run --rm -v `$(PWD)/data:/app/data retail-lakehouse:latest make run-all

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
"@

New-File "$Root\pyproject.toml" @"
[project]
name = "retail-lakehouse"
version = "0.2.0"
description = "Retail Sales Modern Data Lakehouse - Production Grade"
requires-python = ">=3.11"
dependencies = [
    "polars",
    "pyarrow",
    "duckdb",
    "dbt-duckdb",
    "great-expectations",
    "pydantic-settings",
    "structlog",
    "pyyaml",
    "tenacity",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "ipykernel"]

[tool.uv]
dev-dependencies = ["pytest", "ruff"]
"@

New-File "$Root\Dockerfile" @"
FROM python:3.11-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:`$PATH"
ENV PYTHONPATH=/app
CMD ["make", "run-all"]
"@

New-File "$Root\.dockerignore" @"
data/
logs/
reports/
__pycache__/
*.pyc
.git
.env
"@

New-File "$Root\.env.example" @"
# === ENVIRONMENT & SECRETS ===
ENV=dev
LOG_LEVEL=INFO

# Storage override (nếu cần)
# STORAGE_ROOT=data
# BATCH_SIZE=50000
"@

New-File "$Root\.gitignore" @"
__pycache__/
*.pyc
.env
uv.lock
.venv/
data/raw/
data/bronze/
data/silver/
data/gold/
logs/
reports/
.dbt/
"@

# ── Pipeline Core (Config Foundation) ─────────────────────────
New-Dir "$Root\pipeline"
New-File "$Root\pipeline\__init__.py" @"
from .config import settings
from .logging import logger

__all__ = ["settings", "logger", "Settings"]
"@

New-File "$Root\pipeline\config.py" @"
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal
from pathlib import Path
import yaml

class Settings(BaseSettings):
    """Centralized Configuration - Production Grade
    Quy tắc ưu tiên: .env > settings.yml > default
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENV: Literal["dev", "staging", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    STORAGE_ROOT: str = "data"
    BATCH_SIZE: int = Field(100_000, ge=10_000, le=1_000_000)
    MAX_WORKERS: int = Field(4, ge=1, le=16)

    STRUCTLOG_JSON: bool = True
    LOG_FILE: str = "logs/pipeline.log"
    ENABLE_GREAT_EXPECTATIONS: bool = True

    _yaml_config: dict = {}

    def model_post_init(self, __context):
        self._load_yaml_config()

    def _load_yaml_config(self):
        yaml_path = Path("config/settings.yml")
        if not yaml_path.exists():
            return
        with open(yaml_path, encoding="utf-8") as f:
            self._yaml_config = yaml.safe_load(f) or {}

        storage = self._yaml_config.get("storage", {})
        pipeline = self._yaml_config.get("pipeline", {})
        logging_cfg = self._yaml_config.get("logging", {})

        if "STORAGE_ROOT" not in self.model_fields_set and "root" in storage:
            self.STORAGE_ROOT = storage["root"]
        if "BATCH_SIZE" not in self.model_fields_set and "batch_size" in pipeline:
            self.BATCH_SIZE = pipeline["batch_size"]
        if "MAX_WORKERS" not in self.model_fields_set and "max_workers" in pipeline:
            self.MAX_WORKERS = pipeline["max_workers"]
        if "STRUCTLOG_JSON" not in self.model_fields_set and "json_format" in logging_cfg:
            self.STRUCTLOG_JSON = logging_cfg["json_format"]
        if "LOG_FILE" not in self.model_fields_set and "log_file" in logging_cfg:
            self.LOG_FILE = logging_cfg["log_file"]

    def get_layer_path(self, layer: str) -> Path:
        base = Path(self.STORAGE_ROOT).resolve()
        mapping = {
            "bronze": base / "bronze",
            "silver": base / "silver",
            "gold": base / "gold",
            "rejected": base / "silver" / "silver_rejected",
        }
        return mapping.get(layer.lower(), base)

    def ensure_directories(self) -> None:
        for layer in ["bronze", "silver", "gold", "rejected"]:
            self.get_layer_path(layer).mkdir(parents=True, exist_ok=True)
        Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path("reports/data_quality").mkdir(parents=True, exist_ok=True)
        Path("reports/monitoring").mkdir(parents=True, exist_ok=True)

settings: Settings = Settings()
"@

New-File "$Root\pipeline\logging.py" @"
import structlog
import logging
import sys
from pathlib import Path
from .config import settings

def setup_logging():
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.STRUCTLOG_JSON:
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        logger_factory=structlog.WriteLoggerFactory(
            file=Path(settings.LOG_FILE).open("a", encoding="utf-8", errors="ignore")
        ),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=settings.LOG_LEVEL, format="%(message)s", stream=sys.stdout, force=True)
    logger = structlog.get_logger("retail_lakehouse")
    logger.info("🚀 Structured logging initialized", env=settings.ENV, log_level=settings.LOG_LEVEL)
    return logger

logger = setup_logging()
"@

New-File "$Root\pipeline\utils.py" "# Shared utilities - sẽ triển khai sau"
New-File "$Root\pipeline\orchestrator.py" "# Main Pipeline Orchestrator - sẽ triển khai sau"

# ── Các Layer khác (chỉ tạo khung) ───────────────────────────
New-Dir "$Root\pipeline\bronze"
New-File "$Root\pipeline\bronze\__init__.py"
New-File "$Root\pipeline\bronze\ingestor.py" "# Bronze Layer"

New-Dir "$Root\pipeline\silver"
New-File "$Root\pipeline\silver\__init__.py"
New-File "$Root\pipeline\silver\cleaner.py" "# Silver Layer"

New-Dir "$Root\pipeline\gold"
New-File "$Root\pipeline\gold\__init__.py"
New-File "$Root\pipeline\gold\fact_sales.py" "# Gold Layer"

# ── Config & Other Folders ───────────────────────────────────
New-Dir "$Root\config"
New-File "$Root\config\settings.yml" @"
project:
  name: "Retail Sales Modern Data Lakehouse"
  version: "0.2.0"

storage:
  root: "data"

pipeline:
  batch_size: 100000
  max_workers: 4

logging:
  json_format: true
  log_file: "logs/pipeline.log"

data_quality:
  great_expectations_enabled: true
"@

New-Dir "$Root\expectations"
New-File "$Root\expectations\sales_suite.json" "{}"

New-Dir "$Root\reports\data_quality"
New-Dir "$Root\reports\monitoring"
New-Dir "$Root\docs"
New-Dir "$Root\tests\unit"
New-Dir "$Root\tests\integration"
New-Dir "$Root\tests\fixtures"
New-Dir "$Root\scripts"
New-Dir "$Root\logs"
New-Dir "$Root\data\raw\sales"
New-Dir "$Root\data\raw\customer"
New-Dir "$Root\data\raw\product"
New-Dir "$Root\data\bronze"
New-Dir "$Root\data\silver\silver_rejected"
New-Dir "$Root\data\gold"

New-File "$Root\data\.gitignore" "# No data committed"
New-File "$Root\logs\.gitignore" "*"

# ── GitHub CI ────────────────────────────────────────────────
New-Dir "$Root\.github\workflows"
New-File "$Root\.github\workflows\ci.yml" @"
name: CI Pipeline
on: [push, pull_request]
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: make lint
      - run: make test
"@

# ── Kết thúc ─────────────────────────────────────────────────
Write-Host "  Done! Cấu trúc Production Full (uv + Config Foundation) đã được tạo tại: $Root" -ForegroundColor Green
Write-Host ""
Write-Host "  Các bước tiếp theo:" -ForegroundColor Yellow
Write-Host "    cd $Root" -ForegroundColor White
Write-Host "    uv sync                    # Cài dependencies" -ForegroundColor White
Write-Host "    cp .env.example .env        # Tạo file môi trường" -ForegroundColor White
Write-Host "    uv run python -c 'from pipeline.config import settings; settings.ensure_directories()'" -ForegroundColor White
Write-Host "    make run-all                # Chạy pipeline (sau khi implement)" -ForegroundColor White
Write-Host ""
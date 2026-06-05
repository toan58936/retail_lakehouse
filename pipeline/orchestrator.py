# Main Pipeline Coordinator
# pipeline/orchestrator.py
import subprocess
import sys
import os
from pathlib import Path
from pipeline.config import settings
from pipeline.logging import logger
from pipeline.bronze.ingestor import ingest_all_raw_data
from pipeline.silver.cleaner import clean_entity
from pipeline.silver.quality import validate_and_route


def _dbt_env_paths(env_mode: str = "production") -> tuple[Path, Path]:
    """Return absolute Silver input directory and DuckDB output path for dbt."""
    storage_root = Path(settings.STORAGE_ROOT).resolve()

    if env_mode == "sample":
        silver_dir = storage_root / "sample_env" / "silver"
        duckdb_path = storage_root / "sample_env" / "gold" / "lakehouse.duckdb"
    else:
        silver_dir = storage_root / "silver"
        duckdb_path = storage_root / "gold" / "lakehouse.duckdb"

    return silver_dir, duckdb_path


def _prepare_dbt_environment(env_mode: str = "production") -> dict:
    """Prepare dbt environment variables and required local folders."""
    silver_dir, duckdb_path = _dbt_env_paths(env_mode)
    silver_dir.mkdir(parents=True, exist_ok=True)
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    # Force absolute, deterministic paths for dbt-duckdb (avoid adapter rewriting /app/*)
    env["DBT_SILVER_DIR"] = str(silver_dir)
    env["DBT_DB_PATH"] = str(duckdb_path)

    # Additionally pass dbt vars explicitly so Jinja `var('DBT_*')` always resolves correctly.
    # Use forward slashes to reduce path mangling issues inside duckdb adapter.
    env["DBT_CI_VARS"] = (
        f"{{\"DBT_SILVER_DIR\":\"{silver_dir.as_posix()}\",\"DBT_DB_PATH\":\"{duckdb_path.as_posix()}\"}}"
    )

    return env


def run_dbt_command(command: list, env_mode: str = "production") -> bool:
    """Chạy lệnh dbt với hỗ trợ Sandbox environment"""
    try:
        env = _prepare_dbt_environment(env_mode)

        # If dbt vars are provided via env (used for deterministic duckdb external_location paths),
        # append `--vars` to the dbt command to ensure Jinja `var('DBT_*')` resolves correctly.
        cmd = list(command)
        if "DBT_CI_VARS" in env and cmd and cmd[0] == "dbt":
            if not any(arg.startswith("--vars") for arg in cmd):
                cmd.extend(["--vars", env["DBT_CI_VARS"]])

        result = subprocess.run(
            cmd,
            cwd="dbt",
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("dbt command executed successfully", command=" ".join(command), env=env_mode)
            return True
        else:
            logger.error("dbt command failed", 
                        command=" ".join(command), 
                        env=env_mode,
                        stdout=result.stdout,
                        stderr=result.stderr)
            return False

    except Exception as e:
        logger.error("Failed to run dbt command", error=str(e))
        return False


def run_pipeline(env_mode: str = "production") -> None:
    """Chạy toàn bộ End-to-End Pipeline"""
    logger.info(f"=== STARTING FULL PIPELINE [{env_mode.upper()}] ===")

    # Bước 1: Bronze Layer
    logger.info("--- [1/4] BRONZE LAYER ---")
    ingest_all_raw_data(env_mode=env_mode)

    # Bước 2: Silver Layer
    logger.info("--- [2/4] SILVER LAYER ---")
    silver_summaries = []
    for entity in ["customers", "products", "sales"]:
        lf = clean_entity(entity, env_mode=env_mode)
        silver_summaries.append(validate_and_route(lf, entity, env_mode=env_mode))

    failed_entities = [
        summary["entity"]
        for summary in silver_summaries
        if summary["rows_in"] == 0 or summary["rows_valid"] == 0 or summary["valid_file"] is None
    ]
    if failed_entities:
        logger.error("Pipeline stopped due to Silver failure", failed_entities=failed_entities)
        sys.exit(1)

    # Bước 3: Gold Layer - Build
    logger.info("--- [3/4] GOLD LAYER - BUILD ---")

    # Snapshot layer bị lỗi path (/app/*) trong môi trường hiện tại.
    # Tạm skip snapshot để ưu tiên chạy marts/test theo quy trình hiện tại.
    # Khi snapshot đã được fix triệt để, bật lại block này.

    dbt_run_success = run_dbt_command(["dbt", "run", "--select", "+marts"], env_mode)

    if not dbt_run_success:
        logger.error("Pipeline stopped due to dbt run failure")
        sys.exit(1)


    # Bước 4: Gold Layer - Test
    logger.info("--- [4/4] GOLD LAYER - TEST ---")
    dbt_test_success = run_dbt_command(["dbt", "test", "--select", "marts"], env_mode)
    if not dbt_test_success:
        logger.error("Pipeline stopped due to dbt test failure")
        sys.exit(1)

    logger.info(f"=== PIPELINE COMPLETED SUCCESSFULLY [{env_mode.upper()}] ===")

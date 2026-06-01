# pipeline/config.py
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

    # Environment
    ENV: Literal["dev", "staging", "prod"] = "dev"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Storage
    STORAGE_ROOT: str = "data"

    # Pipeline
    BATCH_SIZE: int = Field(100_000, ge=10_000, le=1_000_000)
    MAX_WORKERS: int = Field(4, ge=1, le=16)

    # Logging
    STRUCTLOG_JSON: bool = True
    LOG_FILE: str = "logs/pipeline.log"

    # Data Quality
    ENABLE_GREAT_EXPECTATIONS: bool = True

    # Private
    _yaml_config: dict = {}

    def model_post_init(self, __context):
        """Load YAML sau khi Pydantic load .env"""
        self._load_yaml_config()

    def _load_yaml_config(self):
        """Load settings.yml với tôn trọng ưu tiên .env"""
        yaml_path = Path("config/settings.yml")
        if not yaml_path.exists():
            return

        with open(yaml_path, encoding="utf-8") as f:
            self._yaml_config = yaml.safe_load(f) or {}

        storage = self._yaml_config.get("storage", {})
        pipeline = self._yaml_config.get("pipeline", {})
        logging_cfg = self._yaml_config.get("logging", {})

        # CHỈ override từ YAML nếu .env CHƯA set giá trị
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
        """Lấy đường dẫn layer một cách an toàn"""
        base = Path(self.STORAGE_ROOT).resolve()
        mapping = {
            "bronze": base / "bronze",
            "silver": base / "silver",
            "gold": base / "gold",
            "rejected": base / "silver" / "silver_rejected",
        }
        return mapping.get(layer.lower(), base)

    def ensure_directories(self) -> None:
        """Tạo thư mục động theo config"""
        # Tạo thư mục data layers
        for layer in ["bronze", "silver", "gold", "rejected"]:
            self.get_layer_path(layer).mkdir(parents=True, exist_ok=True)

        # Tạo thư mục log theo LOG_FILE (linh hoạt)
        Path(self.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

        # Reports
        Path("reports/data_quality").mkdir(parents=True, exist_ok=True)
        Path("reports/monitoring").mkdir(parents=True, exist_ok=True)


# Global instance
settings: Settings = Settings()
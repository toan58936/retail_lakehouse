# pipeline/logging.py
import structlog
import sys
import logging
from pathlib import Path
from .config import settings

def setup_logging() -> structlog.BoundLogger:
    """Cấu hình Structured Logging với structlog"""
    
    # Processors chung
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Renderer
    if settings.STRUCTLOG_JSON:
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # =========================================================================
    # VÁ LỖI (CRITICAL FIX): Đảm bảo thư mục chứa file log phải tồn tại
    # trước khi gọi hàm open(), ngăn chặn lỗi FileNotFoundError khi khởi tạo.
    # =========================================================================
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=processors,
        logger_factory=structlog.WriteLoggerFactory(
            file=log_file_path.open("a", encoding="utf-8", errors="ignore")
        ),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL)
        ),
        cache_logger_on_first_use=True,
    )

    # Cấu hình logging chuẩn Python để tương thích
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(message)s",
        stream=sys.stdout,
        force=True
    )

    logger = structlog.get_logger("retail_lakehouse")

    logger.info("🚀 Structured logging initialized", 
               env=settings.ENV,
               log_level=settings.LOG_LEVEL,
               json_output=settings.STRUCTLOG_JSON,
               log_file=settings.LOG_FILE)

    return logger


# Global logger instance
logger: structlog.BoundLogger = setup_logging()
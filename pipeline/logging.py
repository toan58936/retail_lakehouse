# pipeline/logging.py
import structlog
import logging
import sys
from pathlib import Path
from .config import settings

def setup_logging() -> structlog.BoundLogger:
    """Cấu hình Structured Logging xuất song song ra 2 luồng (Console & File)"""
    
    # 1. Đảm bảo thư mục chứa file log phải tồn tại
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Các bộ xử lý chung (Shared processors) dùng chung cho cả File và Console
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # 3. Kết nối Structlog với Standard Logging của Python
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 4. Định dạng ĐẦU RA (Formatters) cho từng luồng
    # - Formatter cho Console: Màu sắc, dễ đọc cho con người
    console_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.dev.ConsoleRenderer(colors=True),
    )
    
    # - Formatter cho File: Định dạng JSON chuẩn hệ thống (hoặc text thường tuỳ config)
    if settings.STRUCTLOG_JSON:
        file_processor = structlog.processors.JSONRenderer(ensure_ascii=False)
    else:
        file_processor = structlog.dev.ConsoleRenderer(colors=False)
        
    file_formatter = structlog.stdlib.ProcessorFormatter(
        processor=file_processor,
    )

    # 5. Cấu hình các "Đường ống" (Handlers) để bắn log đi
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Dọn dẹp handler cũ (Tránh in lặp dòng log)
    root_logger.handlers.clear()

    # Luồng 1: Bắn ra màn hình Terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Luồng 2: Ghi âm thầm vào File
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # 6. Khởi tạo logger và test ngay
    logger = structlog.get_logger("retail_lakehouse")

    logger.info("Structured logging initialized (Dual Stream)", 
               env=settings.ENV,
               log_level=settings.LOG_LEVEL,
               json_output=settings.STRUCTLOG_JSON,
               log_file=settings.LOG_FILE)

    return logger

# Global logger instance
logger: structlog.BoundLogger = setup_logging()

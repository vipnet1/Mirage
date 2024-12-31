import logging
from pathlib import Path
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
import time
import consts


def configure_logger() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(consts.LOGGING_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    formatter.converter = time.gmtime

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_logging_filter)

    log_file = Path(consts.LOG_FOLDER) / Path(f"log_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=consts.LOGGING_MAX_BYTES, backupCount=consts.LOGGING_BACKUP_COUNT)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_logging_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def _logging_filter(record: logging.LogRecord) -> bool:
    message = record.getMessage()
    if 'HTTP Request: POST https://api.telegram.org/bot' in message:
        return False

    if 'Exception happened while polling for updates' in message:
        return False

    if 'HTTP/1.1" 404' in message:
        return False

    return True

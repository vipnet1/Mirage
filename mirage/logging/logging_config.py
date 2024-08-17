import logging
from pathlib import Path
import datetime
from logging.handlers import RotatingFileHandler
import consts


def configure_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(consts.LOGGING_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_logging_filter)

    log_file = Path(consts.LOG_FOLDER) / Path(f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=consts.LOGGING_MAX_BYTES, backupCount=consts.LOGGING_BACKUP_COUNT)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(_logging_filter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def _logging_filter(record: logging.LogRecord):
    message = record.getMessage()
    if 'HTTP Request: POST https://api.telegram.org/bot' in message:
        return False

    return True

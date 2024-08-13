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

    log_file = Path(consts.LOG_FOLDER) / Path(f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")
    file_handler = RotatingFileHandler(log_file, maxBytes=consts.LOGGING_MAX_BYTES, backupCount=consts.LOGGING_BACKUP_COUNT)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

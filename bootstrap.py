from pathlib import Path
from mirage import consts


def bootstrap():
    Path(consts.GENERAL_CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.BROKER_CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.STRATEGY_CONFIG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.LOG_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(consts.DATABASES_FOLDER).mkdir(parents=True, exist_ok=True)

import importlib


class MirageImportsException(Exception):
    pass


def import_object(file_name: str, function_name: str):
    try:
        module = importlib.import_module(file_name)
        return getattr(module, function_name)
    except ImportError as e:
        raise MirageImportsException from e

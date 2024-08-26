from dataclasses import dataclass, asdict
from typing import Any, Dict


def dataclass_to_dict(data: dataclass) -> Dict[str, Any]:
    return clean_dict(asdict(data))


def clean_dict(record: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in record.items() if v is not None}

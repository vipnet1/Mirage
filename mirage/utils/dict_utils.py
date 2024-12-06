from dataclasses import dataclass, asdict


def dataclass_to_dict(data: dataclass) -> dict[str, any]:
    return clean_dict(asdict(data))


def clean_dict(record: dict[str, any]) -> dict[str, any]:
    return {k: v for k, v in record.items() if v is not None}

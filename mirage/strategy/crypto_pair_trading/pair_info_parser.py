
from dataclasses import dataclass


@dataclass
class PairInfo:
    first_pair: str
    second_pair: str
    ratio: float


class PairInfoParser():
    def __init__(self, pair_raw: str, base_currency: str):
        self._pair_raw = pair_raw
        self._base_currency = base_currency

    def parse_pair_info(self) -> PairInfo:
        parts = self._pair_raw.split('-')

        first_pair = self._remove_exchange_name(parts[0])
        ratio_string = self._remove_exchange_name(parts[1])

        second_pair, ratio = self._extract_ratio_and_string(ratio_string)

        return PairInfo(self._add_slash_to_pair(first_pair), self._add_slash_to_pair(second_pair), ratio)

    def _extract_ratio_and_string(self, ratio_string: str) -> tuple[str, float]:
        parts = ratio_string.split('*')

        if len(parts) == 1:
            return parts[0], 1

        try:
            ratio = float(parts[0])
            symbol = parts[1]
        except ValueError:
            ratio = float(parts[1])
            symbol = parts[0]

        return symbol, ratio

    def _remove_exchange_name(self, pair: str) -> str:
        star = pair.find('*')
        colon = pair.find(':')
        if colon == -1:
            return pair

        if star != -1 and star < colon:
            return pair[0:star+1] + pair[colon+1:]

        return pair[colon+1:]

    def _add_slash_to_pair(self, pair: str) -> str:
        base_currency = pair.replace(self._base_currency, "")
        return f'{base_currency}/{self._base_currency}'

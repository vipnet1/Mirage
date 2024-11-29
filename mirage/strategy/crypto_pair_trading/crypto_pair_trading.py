from dataclasses import dataclass
import logging
from typing import Optional, Tuple

import pymongo
import consts
from mirage.algorithm.borrow import borrow_algorithm
from mirage.algorithm.fetch_tickers import fetch_tickers_algorithm
from mirage.algorithm.simple_order import simple_order_algorithm
from mirage.database.mongo.base_db_record import BaseDbRecord
from mirage.database.mongo.common_operations import insert_dataclass, update_dataclass
from mirage.database.mongo.db_config import DbConfig
from mirage.strategy.strategy import Strategy, StrategyException
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils import symbol_utils
from mirage.utils.dict_utils import dataclass_to_dict
from mirage.utils.symbol_utils import get_base_symbol


class CryptoPairTradingException(StrategyException):
    pass


@dataclass
class PairInfo:
    first_pair: str
    second_pair: str
    ratio: float


@dataclass
class PositionInfo(BaseDbRecord):
    request_data_id: Optional[str] = None
    strategy_instance: Optional[str] = None

    chart_pair: Optional[str] = None

    side: Optional[str] = None
    pair: Optional[str] = None

    is_open: Optional[bool] = None

    first_amount: Optional[float] = None
    second_amount: Optional[float] = None


class CryptoPairTrading(Strategy):
    description = 'Go long & short on pairs. Binance margin account.'

    CONFIG_KEY_MAX_LOSS_PERCENT = 'strategy.max_loss_percent'
    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'

    DATA_PAIR = 'pair'
    DATA_ACTION = 'action'
    DATA_SIDE = 'side'
    DATA_STOPLOSS_DISTANCE = 'stoploss_distance'

    ACTION_ENTRY = 'entry'
    ACTION_EXIT = 'exit'

    SIDE_LONG = 'long'
    SIDE_SHORT = 'short'

    def __init__(
            self,
            request_data_id: str,
            strategy_data: dict[str, any],
            strategy_name: str,
            strategy_instance: str,
    ):
        super().__init__(request_data_id, strategy_data, strategy_name, strategy_instance)
        self._existing_position = None
        self._pair_info = None
        self._coin1_amount = None
        self._coin2_amount = None

    async def should_execute_strategy(self) -> bool:
        self._existing_position = self._get_recent_position_info()

        pair_raw = self.strategy_data.get(CryptoPairTrading.DATA_PAIR)
        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)

        self._pair_info = self._parse_pair_info()
        self._validate_pair_info_from_base_currency()

        if action == CryptoPairTrading.ACTION_ENTRY:
            if self._existing_position:
                logging.warning("Can't enter new position: another one exists with the chart pair %s", pair_raw)
                return False

            self._coin1_amount, self._coin2_amount = self._calculate_positions_for_coins()
            await self._validate_can_enter_position()

        elif action == CryptoPairTrading.ACTION_EXIT:
            if not self._existing_position:
                logging.warning("Can't exit position as not in active with chart pair %s", pair_raw)
                return False
        else:
            raise CryptoPairTradingException(f'Invalid action {action} with chart pair {pair_raw}')

        return True

    async def execute(self) -> StrategyExecutionStatus:
        await super().execute()

        existing_position = self._get_recent_position_info()
        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)

        if action == CryptoPairTrading.ACTION_ENTRY:
            await self._enter_new_position()
            return StrategyExecutionStatus.ONGOING
        elif action == CryptoPairTrading.ACTION_EXIT:
            await self._exit_current_position(existing_position)
            return StrategyExecutionStatus.RETURN_FUNDS

        raise CryptoPairTradingException('Invalid action - should not get there! This had to be already checked.')

    def _get_recent_position_info(self) -> Optional[PositionInfo]:
        recent_position = self._get_recent_position_info_from_db()
        if recent_position is None:
            return None

        position_info = PositionInfo(**recent_position)
        if not position_info.is_open:
            return None

        return position_info

    async def _enter_new_position(self):
        pair_raw = self.strategy_data.get(CryptoPairTrading.DATA_PAIR)
        side = self.strategy_data.get(CryptoPairTrading.DATA_SIDE)

        if side == CryptoPairTrading.SIDE_LONG:
            await self._binance_enter_new_position(self._pair_info.first_pair, self._coin1_amount, self._pair_info.second_pair, self._coin2_amount)
        elif side == CryptoPairTrading.SIDE_SHORT:
            await self._binance_enter_new_position(self._pair_info.second_pair, self._coin2_amount, self._pair_info.first_pair, self._coin1_amount)
        else:
            raise CryptoPairTradingException(f'Invalid side received {side} with chart pair {pair_raw}')

        pair = self._pair_info.first_pair.split('/')[0] + '/' + self._pair_info.second_pair.split('/')[0]
        insert_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(
                request_data_id=self.request_data_id,
                strategy_instance=self.strategy_instance,
                chart_pair=self.strategy_data.get(CryptoPairTrading.DATA_PAIR),
                side=side,
                pair=pair,
                is_open=True,
                first_amount=self._coin1_amount,
                second_amount=self._coin2_amount
            )
        )

    async def _binance_enter_new_position(self, long_pair: str, long_amount: float, short_pair: str, short_amount: float):
        await borrow_algorithm.BorrowAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                borrow_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Pair trading borrow short coin',
                    operation=borrow_algorithm.BorrowAlgorithm.OPERATION_BORROW,
                    symbol=get_base_symbol(short_pair),
                    amount=short_amount
                )
            ]
        ).execute()

        await simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading long coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=long_pair,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_BUY,
                    amount=long_amount,
                    price=None
                ),
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading short coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=short_pair,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_SELL,
                    amount=short_amount,
                    price=None
                )
            ]
        ).execute()

    async def _exit_current_position(self, position_info: PositionInfo):
        if position_info.side == CryptoPairTrading.SIDE_LONG:
            await self._binance_exit_current_position(
                self._pair_info.first_pair, position_info.first_amount, self._pair_info.second_pair, position_info.second_amount
            )
        elif position_info.side == CryptoPairTrading.SIDE_SHORT:
            await self._binance_exit_current_position(
                self._pair_info.second_pair, position_info.second_amount, self._pair_info.first_pair, position_info.first_amount
            )
        else:
            raise CryptoPairTradingException(f'Invalid side when exiting position {position_info.side}')

        update_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(_id=position_info._id),
            PositionInfo(is_open=False)
        )

    async def _binance_exit_current_position(self, long_pair: str, long_amount: float, short_pair: str, short_amount: float):
        await simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading sell longed coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=long_pair,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_SELL,
                    amount=long_amount,
                    price=None
                ),
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading buy shorted coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=short_pair,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_BUY,
                    amount=short_amount,
                    price=None
                )
            ]
        ).execute()

        await borrow_algorithm.BorrowAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                borrow_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Pair trading repay borrowed short coin',
                    operation=borrow_algorithm.BorrowAlgorithm.OPERATION_REPAY,
                    symbol=get_base_symbol(short_pair),
                    amount=short_amount
                )
            ]
        ).execute()

    def _get_recent_position_info_from_db(self):
        return DbConfig.client[consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING][consts.COLLECTION_POSITION_INFO].find_one(
            dataclass_to_dict(PositionInfo(strategy_instance=self.strategy_instance)),
            sort=[(consts.RECORD_KEY_CREATED_AT, pymongo.DESCENDING)]
        )

    def _parse_pair_info(self) -> PairInfo:
        pair_raw = self.strategy_data.get(CryptoPairTrading.DATA_PAIR)

        parts = pair_raw.split('-')
        first_pair, ratio_string = parts

        ratio_parts = ratio_string.split('*')
        ratio = int(ratio_parts[0])
        second_pair = ratio_parts[1]

        return PairInfo(first_pair, second_pair, ratio)

    def _calculate_positions_for_coins(self) -> Tuple[float, float]:
        max_loss_percent = self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_MAX_LOSS_PERCENT)
        stoploss_distance = self.strategy_data.get(CryptoPairTrading.DATA_STOPLOSS_DISTANCE)

        coin1_amount = self.allocated_capital.variable * (max_loss_percent / 100) / stoploss_distance
        coin2_amount = coin1_amount * self._pair_info.ratio

        return coin1_amount, coin2_amount

    def _validate_pair_info_from_base_currency(self) -> None:
        base_currency = self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_BASE_CURRENCY)
        if (symbol_utils.get_quote_symbol(self._pair_info.first_pair) != base_currency
                or symbol_utils.get_quote_symbol(self._pair_info.second_pair) != base_currency):
            raise CryptoPairTradingException('Pair quote currency does not match config base currency - {base_currency}')

    async def _validate_can_enter_position(self) -> None:
        """
        Allow going long using strategy capital only. The short pair borrowed.
        Anyway check that each one of coins amount * price value less than strategy capital, because
        longed & shorted mount should be more less the same should be fine.
        """
        fta = fetch_tickers_algorithm.FetchTickersAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                fetch_tickers_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Fetching pair trading coins price to check if enough funds to enter position',
                    symbols=[self._pair_info.first_pair, self._pair_info.second_pair],
                )
            ]
        )
        await fta.execute()

        results = fta.command_results[0]
        self._validate_pair_cost_fine(self._pair_info.first_pair, results[self._pair_info.first_pair]['last'], self._coin1_amount)
        self._validate_pair_cost_fine(self._pair_info.second_pair, results[self._pair_info.second_pair]['last'], self._coin2_amount)

    def _validate_pair_cost_fine(self, pair: str, price: float, amount: float):
        total = price * amount
        if total >= self.allocated_capital.variable:
            raise CryptoPairTradingException(f'Need to buy/borrow {total} of pair {pair}, but max is {self.allocated_capital.variable}')

from dataclasses import dataclass
import logging
from typing import Optional

import pymongo
import consts
from mirage.algorithm.borrow import borrow_algorithm
from mirage.algorithm.fetch_tickers import fetch_tickers_algorithm
from mirage.algorithm.simple_order import simple_order_algorithm
from mirage.database.mongo.base_db_record import BaseDbRecord
from mirage.database.mongo.common_operations import insert_dataclass, update_dataclass
from mirage.database.mongo.db_config import DbConfig
from mirage.strategy.crypto_pair_trading.pair_info_parser import PairInfoParser
from mirage.strategy.strategy import Strategy, StrategyException
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.dict_utils import dataclass_to_dict
from mirage.utils.symbol_utils import get_base_symbol


class CryptoPairTradingException(StrategyException):
    pass


@dataclass
class PositionInfo(BaseDbRecord):
    request_data_id: Optional[str] = None
    strategy_instance: Optional[str] = None
    indicator: Optional[str] = None

    chart_pair: Optional[str] = None

    side: Optional[str] = None
    pair: Optional[str] = None

    is_open: Optional[bool] = None

    longed_coin: Optional[str] = None
    longed_amount: Optional[float] = None

    shorted_coin: Optional[str] = None
    shorted_amount: Optional[float] = None


class CryptoPairTrading(Strategy):
    description = 'Go long & short on pairs. Binance margin account.'

    CONFIG_KEY_MAX_LOSS_PERCENT = 'strategy.max_loss_percent'
    CONFIG_KEY_BASE_CURRENCY = 'strategy_manager.base_currency'

    DATA_ACTION = 'action'
    DATA_PAIR = 'pair'
    DATA_SIDE = 'side'
    DATA_PRICE = 'price'
    DATA_STOPLOSS_PRICE = 'stoploss_price'

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
        self._longed_coin = None
        self._longed_amount = None
        self._shorted_coin = None
        self._shorted_amount = None

    def is_entry(self) -> bool:
        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)
        return action == CryptoPairTrading.ACTION_ENTRY

    async def should_execute_strategy(self) -> bool:
        self._existing_position = self._get_recent_position_info()

        pair_raw = self.strategy_data.get(CryptoPairTrading.DATA_PAIR)
        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)

        base_currency = self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_BASE_CURRENCY)
        self._pair_info = PairInfoParser(pair_raw, base_currency).parse_pair_info()

        if action == CryptoPairTrading.ACTION_ENTRY:
            if self._existing_position:
                logging.warning(
                    "Can't enter new position: another one exists. Strategy instance %s, pair %s", self._existing_position.strategy_instance, pair_raw
                )
                return False

            side = self.strategy_data.get(CryptoPairTrading.DATA_SIDE)
            if side not in [self.SIDE_LONG, self.SIDE_SHORT]:
                raise CryptoPairTradingException(f'Invalid side received {side} with chart pair {pair_raw}')

            await self._fetch_coins_amounts(side)
            # available = await self._get_available_borrow_funds()
            # if self._borrow_amount > available:
            #     logging.warning(
            #         "Can't borrow coin %s. Needed: %s, Available: %s. Ignoring request.", self._borrow_coin, available, self._borrow_amount
            #     )
            #     return False

        elif action == CryptoPairTrading.ACTION_EXIT:
            if not self._existing_position:
                logging.warning("Can't exit position as not in active with chart pair %s", pair_raw)
                return False

            self._longed_coin = self._existing_position.longed_coin
            self._longed_amount = self._existing_position.longed_amount
            self._shorted_coin = self._existing_position.shorted_coin
            self._shorted_amount = self._existing_position.shorted_amount
        else:
            raise CryptoPairTradingException(f'Invalid action {action} with chart pair {pair_raw}')

        return True

    async def execute(self) -> StrategyExecutionStatus:
        await super().execute()

        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)
        if action == CryptoPairTrading.ACTION_ENTRY:
            await self._enter_new_position()
            return StrategyExecutionStatus.ONGOING
        elif action == CryptoPairTrading.ACTION_EXIT:
            await self._exit_current_position(self._existing_position)
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
        side = self.strategy_data.get(CryptoPairTrading.DATA_SIDE)

        if side == CryptoPairTrading.SIDE_LONG:
            await self._binance_enter_new_position()
        else:
            await self._binance_enter_new_position()

        pair = get_base_symbol(self._pair_info.first_pair) + '/' + get_base_symbol(self._pair_info.second_pair)
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
                longed_coin=self._longed_coin,
                longed_amount=self._longed_amount,
                shorted_coin=self._shorted_coin,
                shorted_amount=self._shorted_amount
            )
        )

    async def _binance_enter_new_position(self):
        await borrow_algorithm.BorrowAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                borrow_algorithm.BorrowCommand(
                    strategy=self.__class__.__name__,
                    description='Pair trading borrow short coin',
                    symbol=get_base_symbol(self._shorted_coin),
                    amount=self._shorted_amount
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
                    symbol=self._longed_coin,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_BUY,
                    amount=self._longed_amount,
                    price=None
                ),
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading short coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=self._shorted_coin,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_SELL,
                    amount=self._shorted_amount,
                    price=None
                )
            ]
        ).execute()

    async def _exit_current_position(self, position_info: PositionInfo):
        if position_info.side == CryptoPairTrading.SIDE_LONG:
            await self._binance_exit_current_position()
        elif position_info.side == CryptoPairTrading.SIDE_SHORT:
            await self._binance_exit_current_position()
        else:
            raise CryptoPairTradingException(f'Invalid side when exiting position {position_info.side}')

        update_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(_id=position_info._id),
            PositionInfo(is_open=False)
        )

    async def _binance_exit_current_position(self):
        await simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading sell longed coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=self._longed_coin,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_SELL,
                    amount=self._longed_amount,
                    price=None
                ),
                simple_order_algorithm.CommandAmount(
                    strategy=self.__class__.__name__,
                    description='Pair trading buy shorted coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=self._shorted_coin,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_BUY,
                    amount=self._shorted_amount,
                    price=None
                )
            ]
        ).execute()

        await borrow_algorithm.BorrowAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                borrow_algorithm.RepayCommand(
                    strategy=self.__class__.__name__,
                    description='Pair trading repay borrowed short coin',
                    symbol=get_base_symbol(self._shorted_coin),
                    amount=self._shorted_amount
                )
            ]
        ).execute()

    def _get_recent_position_info_from_db(self):
        return DbConfig.client[consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING][consts.COLLECTION_POSITION_INFO].find_one(
            dataclass_to_dict(PositionInfo(strategy_instance=self.strategy_instance)),
            sort=[(consts.RECORD_KEY_CREATED_AT, pymongo.DESCENDING)]
        )

    async def _fetch_coins_amounts(self, side: str) -> None:
        if side == self.SIDE_LONG:
            self._longed_coin = self._pair_info.first_pair
            self._shorted_coin = self._pair_info.second_pair
        else:
            self._longed_coin = self._pair_info.second_pair
            self._shorted_coin = self._pair_info.first_pair

        fta = fetch_tickers_algorithm.FetchTickersAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                fetch_tickers_algorithm.Command(
                    strategy=self.__class__.__name__,
                    description='Fetching pair trading coins price to check if enough funds to enter position',
                    symbols=[self._longed_coin, self._shorted_coin],
                )
            ]
        )
        await fta.execute()

        results = fta.command_results[0]
        longed_coin_price = results[self._longed_coin]['last']
        shorted_coin_price = results[self._shorted_coin]['last']

        self._longed_amount = 0.5 * self.allocated_capital.variable / longed_coin_price
        self._shorted_amount = 0.5 * self.allocated_capital.variable / shorted_coin_price

    # async def _get_available_borrow_funds(self) -> float:
    #     fta = borrow_algorithm.BorrowAlgorithm(
    #         self.capital_flow,
    #         self.request_data_id,
    #         [
    #             borrow_algorithm.FetchBalanceCommand(
    #                 strategy=self.__class__.__name__,
    #                 description=f'Checking whether enough of coin {self._borrow_coin} to borrow',
    #             )
    #         ]
    #     )
    #     await fta.execute()

    #     results = fta.command_results[0]
    #     available = results['borrow'][self._borrow_coin]
    #     return available

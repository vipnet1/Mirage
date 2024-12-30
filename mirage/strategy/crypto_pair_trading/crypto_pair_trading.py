import logging
from typing import Optional

import pymongo
import consts
from mirage.algorithm.borrow import borrow_algorithm
from mirage.algorithm.borrow.exceptions import NoLendersException
from mirage.algorithm.fetch_tickers import fetch_tickers_algorithm
from mirage.algorithm.simple_order import simple_order_algorithm
from mirage.channels.channels_manager import ChannelsManager
from mirage.database.mongo.common_operations import get_single_record, insert_dataclass, update_dataclass
from mirage.strategy.crypto_pair_trading.exceptions import CryptoPairTradingException, SilentCryptoPairTradingException
from mirage.strategy.crypto_pair_trading.pair_info_parser import PairInfoParser
from mirage.strategy.crypto_pair_trading.position_info import PositionInfo
from mirage.strategy.pre_execution_status import PARAM_TRANSFER_AMOUNT, PreExecutionStatus
from mirage.strategy.strategy import Strategy
from mirage.strategy.strategy_execution_status import StrategyExecutionStatus
from mirage.utils.dict_utils import dataclass_to_dict
from mirage.utils.multi_logging import log_and_send
from mirage.utils.symbol_utils import floor_amount, floor_coin_amount, get_base_symbol


class CryptoPairTrading(Strategy):
    description = 'Go long & short on pairs. Binance margin account.'

    NOTIFY_BIG_RATIO_PERCENT = 30

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

    ACTION_PARAM_NAME = 'name'

    ACTION_NAME_BORROWED = 'borrowed'
    ACTION_NAME_SOLD = 'sold'
    ACTION_NAME_BOUGHT = 'bought'

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
        self._longed_capital = None
        self._shorted_coin = None
        self._shorted_amount = None
        self._shorted_capital = None
        self._transfer_amount = None

    def is_entry(self) -> bool:
        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)
        return action == CryptoPairTrading.ACTION_ENTRY

    async def should_execute_strategy(self, available_capital: float) -> tuple[bool, PreExecutionStatus, dict[str, any]]:
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
                return False, None, None

            side = self.strategy_data.get(CryptoPairTrading.DATA_SIDE)
            if side not in [CryptoPairTrading.SIDE_LONG, CryptoPairTrading.SIDE_SHORT]:
                raise CryptoPairTradingException(f'Invalid side received {side} with chart pair {pair_raw}')

            await self._fetch_coins_amounts(side, available_capital)

        elif action == CryptoPairTrading.ACTION_EXIT:
            if not self._existing_position:
                logging.warning("Can't exit position as not in active with chart pair %s", pair_raw)
                return False, None, None

            self._longed_coin = self._existing_position.longed_coin
            self._longed_amount = self._existing_position.longed_amount
            self._shorted_coin = self._existing_position.shorted_coin
            self._shorted_amount = self._existing_position.shorted_amount
        else:
            raise CryptoPairTradingException(f'Invalid action {action} with chart pair {pair_raw}')

        return True, PreExecutionStatus.PARTIAL_ALLOCATION, {PARAM_TRANSFER_AMOUNT: self._transfer_amount}

    async def execute(self) -> StrategyExecutionStatus:
        await super().execute()

        action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)
        if action == CryptoPairTrading.ACTION_ENTRY:
            await self._try_borrow_funds()
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

    async def _try_borrow_funds(self) -> None:
        try:
            ba = borrow_algorithm.BorrowAlgorithm(
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
            )
            await ba.execute()

            self._actions_track.append({
                CryptoPairTrading.ACTION_PARAM_NAME: CryptoPairTrading.ACTION_NAME_BORROWED
            })

            amount = ba.custom_params[borrow_algorithm.BorrowAlgorithm.PARAM_ACTUALLY_BORROWED_AMOUNT]
            if amount != self._shorted_amount:
                logging.info('Actual borrowed amount changed cause of currency precision to %s', amount)
                self._shorted_amount = amount

        except NoLendersException as exc:
            await log_and_send(
                logging.warning, ChannelsManager.get_communication_channel(),
                f'No lenders to borrow coin {get_base_symbol(self._shorted_coin)}. Skipping entry.'
            )
            raise SilentCryptoPairTradingException() from exc

    async def _enter_new_position(self):
        await self._binance_enter_new_position()

        side = self.strategy_data.get(CryptoPairTrading.DATA_SIDE)
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
                longed_capital=self._longed_capital,
                shorted_coin=self._shorted_coin,
                shorted_amount=self._shorted_amount,
                shorted_capital=self._shorted_capital,
                transfer_amount=self._transfer_amount,
                base_currency=self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_BASE_CURRENCY)
            )
        )

    async def _binance_enter_new_position(self):
        # We first sell then buy to not go into negative funds zone and get exception
        await self._entry_sell_short_coins()
        self._actions_track.append({
            CryptoPairTrading.ACTION_PARAM_NAME: CryptoPairTrading.ACTION_NAME_SOLD
        })

        await self._entry_buy_long_coins()
        self._actions_track.append({
            CryptoPairTrading.ACTION_PARAM_NAME: CryptoPairTrading.ACTION_NAME_BOUGHT
        })

    async def _entry_buy_long_coins(self):
        # As longed amount price may change and we won't have enough funds to buy it, we buy it with cost and then store the amount
        soa = simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
                simple_order_algorithm.CommandCost(
                    strategy=self.__class__.__name__,
                    description='Pair trading long coin',
                    wallet=simple_order_algorithm.SimpleOrderAlgorithm.WALLET_MARGIN,
                    type=simple_order_algorithm.SimpleOrderAlgorithm.TYPE_MARKET,
                    symbol=self._longed_coin,
                    operation=simple_order_algorithm.SimpleOrderAlgorithm.OPERATION_BUY,
                    cost=self._longed_capital,
                    price=None
                )
            ],
        )
        await soa.execute()

        result = soa.command_results[0]
        self._longed_capital = result['cost']
        self._longed_amount = result['amount']

    async def _entry_sell_short_coins(self):
        # As we borrowed exact coins amount we sell this exact amount
        soa = simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
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
            ],
        )
        await soa.execute()

        result = soa.command_results[0]
        self._shorted_capital = result['cost']

    async def _exit_current_position(self, position_info: PositionInfo):
        await self._exit_sell_longed_coins()
        await self._exit_buy_shorted_coins()
        await self._repay_borrowed_funds()

        update_dataclass(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING,
            consts.COLLECTION_POSITION_INFO,
            PositionInfo(_id=position_info._id),
            PositionInfo(is_open=False)
        )

    async def _exit_sell_longed_coins(self):
        # we sell all the longed coins that we bought
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
                )
            ],
        ).execute()

    async def _exit_buy_shorted_coins(self):
        # we need to buy an exact amount of shorted coins to repay them
        await simple_order_algorithm.SimpleOrderAlgorithm(
            self.capital_flow,
            self.request_data_id,
            [
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
            ],
        ).execute()

    async def _repay_borrowed_funds(self):
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
        return get_single_record(
            consts.DB_NAME_STRATEGY_CRYPTO_PAIR_TRADING, consts.COLLECTION_POSITION_INFO,
            dataclass_to_dict(PositionInfo(strategy_instance=self.strategy_instance)),
            sort=[(consts.RECORD_KEY_CREATED_AT, pymongo.DESCENDING)]
        )

    async def _fetch_coins_amounts(self, side: str, available_capital: float) -> None:
        if side == CryptoPairTrading.SIDE_LONG:
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
                    description='Fetching pair trading coins price to calculate amount & cost to enter with',
                    symbols=[self._longed_coin, self._shorted_coin],
                )
            ]
        )
        await fta.execute()

        results = fta.command_results[0]
        longed_coin_price = results[self._longed_coin]['last']
        shorted_coin_price = results[self._shorted_coin]['last']

        logging.info('Longed coin %s price: %s', self._longed_coin, longed_coin_price)
        logging.info('Shorted coin %s price: %s', self._shorted_coin, shorted_coin_price)

        await self._calculate_coins_amounts(longed_coin_price, shorted_coin_price, available_capital)

    async def _calculate_coins_amounts(self, longed_coin_price: float, shorted_coin_price: float, available_capital: float) -> None:
        price = self.strategy_data.get(CryptoPairTrading.DATA_PRICE)
        stoploss = self.strategy_data.get(CryptoPairTrading.DATA_STOPLOSS_PRICE)
        max_loss_percent = self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_MAX_LOSS_PERCENT)

        # max amount to meet stoploss percent lose
        max_amount_can_buy = ((max_loss_percent / 100) * self.allocated_capital.variable) / abs(price - stoploss)

        long_amount = max_amount_can_buy
        short_amount = max_amount_can_buy

        if self._shorted_coin == self._pair_info.second_pair:
            short_amount *= self._pair_info.ratio
        else:
            long_amount *= self._pair_info.ratio

        long_capital = long_amount * longed_coin_price
        short_capital = short_amount * shorted_coin_price
        total_capital = long_capital + short_capital

        # We transfer only long capital, as short we should be able to borrow with the transferred long.
        # if need to spend more than available reduce it.
        capital_ratio = available_capital / long_capital
        if capital_ratio < 1:
            logging.info('Reducing position to match available capital. Wanted to transfer: %s, Available: %s.', long_capital, available_capital)

            long_amount *= capital_ratio
            short_amount *= capital_ratio
            long_capital *= capital_ratio
            short_capital *= capital_ratio
            total_capital *= capital_ratio

        capital_diff = abs(long_capital / short_capital) * 100
        if capital_diff < 100 - CryptoPairTrading.NOTIFY_BIG_RATIO_PERCENT or 100 + CryptoPairTrading.NOTIFY_BIG_RATIO_PERCENT < capital_diff:
            await log_and_send(
                logging.warning, ChannelsManager.get_communication_channel(),
                f'Difference between bought coins {self._longed_coin}, {self._shorted_coin} is too big: {capital_diff}%. '
                f'Still entering position, but consider changing chart ratio to remain market neutral.'
            )

        # floored so math operations won't accidently result larger number leading to an error
        self._transfer_amount = floor_coin_amount(
            self.strategy_instance_config.get(CryptoPairTrading.CONFIG_KEY_BASE_CURRENCY),
            long_capital
        )
        reduction = self._transfer_amount / long_capital

        # ccxt checks number of decimals in each coin and sends request correctly. But Binance may not return this info sometimes.
        # To reduce error rate leave only 8 decimals, as BTC the largest one and uses 8 so it will be fine with other cryptos too.
        # But actually, seems like Binance allows to borrow even the cheapest coins using 8 digits. So it should be good for all coins.
        self._longed_capital = floor_amount(self._transfer_amount * reduction, 8)
        self._shorted_amount = floor_amount(short_amount * reduction, 8)

    async def _exception_revert_internal(self) -> bool:
        data_action = self.strategy_data.get(CryptoPairTrading.DATA_ACTION)
        if data_action != CryptoPairTrading.ACTION_ENTRY:
            return False

        for action_params in reversed(self._actions_track):
            param_name = action_params[CryptoPairTrading.ACTION_PARAM_NAME]

            if param_name == CryptoPairTrading.ACTION_NAME_BOUGHT:
                await self._exit_sell_longed_coins()

            if param_name == CryptoPairTrading.ACTION_NAME_SOLD:
                await self._exit_buy_shorted_coins()

            if param_name == CryptoPairTrading.ACTION_NAME_BORROWED:
                await self._repay_borrowed_funds()

        return True

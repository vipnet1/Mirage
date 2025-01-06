from mirage.performance.mirage_performance import DbTradePerformance


class InstanceInfoProcessor:
    RECORDS_COUNT = 'records_count'
    PNL = 'pnl'
    WINNING_TRADES = 'winning_trades'
    ROI_PERCENT = 'roi_percent'
    MAX_LOSS = 'max_loss'
    MAX_PROFIT = 'max_profit'
    MAX_LOSS_PERCENT = 'max_loss_percent'
    MAX_PROFIT_PERCENT = 'max_profit_percent'
    TOTAL_CAPITAL = 'total_capital'
    TOTAL_WINS = 'total_wins'
    TOTAL_LOSSES = 'total_losses'
    TOTAL_WINS_PERCENT = 'total_wins_percent'
    TOTAL_LOSSES_PERCENT = 'total_losses_percent'
    PROFIT_PERCENTS = 'profit_percents'
    TOTAL_FEES = 'total_fees'
    MAX_FEE = 'max_fee'
    TOTAL_TRADING_CAPITAL_FEE_PERCENTAGE = 'total_trading_capital_fee_percentage'
    MAX_TRADING_CAPITAL_FEE_PERCENTAGE = 'max_trading_capital_fee_percentage'

    def __init__(self, instance_info: dict[str, any], db_trade_performance: DbTradePerformance):
        self._instance_info = instance_info
        self._db_trade_performance = db_trade_performance

    def process(self):
        self._process_records_count()
        self._process_pnl()
        self._process_winning_trades()
        self._process_profit_loss_bounds()
        self._process_roi_percent()
        self._process_total_capital()
        self._process_total_win_lose()
        self._process_profit_percents()
        self._process_fees()

    def _process_records_count(self):
        self._maybe_populate(InstanceInfoProcessor.RECORDS_COUNT, 0)
        self._instance_info[InstanceInfoProcessor.RECORDS_COUNT] += 1

    def _process_pnl(self):
        self._maybe_populate(InstanceInfoProcessor.PNL, 0)
        self._instance_info[InstanceInfoProcessor.PNL] += self._db_trade_performance.profit

    def _process_winning_trades(self):
        self._maybe_populate(InstanceInfoProcessor.WINNING_TRADES, 0)
        if self._db_trade_performance.profit > 0:
            self._instance_info[InstanceInfoProcessor.WINNING_TRADES] += 1

    def _process_profit_loss_bounds(self):
        self._maybe_populate(InstanceInfoProcessor.MAX_PROFIT, 0)
        self._maybe_populate(InstanceInfoProcessor.MAX_PROFIT_PERCENT, 0)
        self._maybe_populate(InstanceInfoProcessor.MAX_LOSS, 0)
        self._maybe_populate(InstanceInfoProcessor.MAX_LOSS_PERCENT, 0)

        profit = self._db_trade_performance.profit
        if profit > self._instance_info[InstanceInfoProcessor.MAX_PROFIT]:
            self._instance_info[InstanceInfoProcessor.MAX_PROFIT] = profit

        if profit < self._instance_info[InstanceInfoProcessor.MAX_LOSS]:
            self._instance_info[InstanceInfoProcessor.MAX_LOSS] = profit

        profit_percent = self._db_trade_performance.profit_percent
        if profit_percent > self._instance_info[InstanceInfoProcessor.MAX_PROFIT_PERCENT]:
            self._instance_info[InstanceInfoProcessor.MAX_PROFIT_PERCENT] = profit_percent

        if profit_percent < self._instance_info[InstanceInfoProcessor.MAX_LOSS_PERCENT]:
            self._instance_info[InstanceInfoProcessor.MAX_LOSS_PERCENT] = profit_percent

    def _process_roi_percent(self):
        self._maybe_populate(InstanceInfoProcessor.ROI_PERCENT, 0)
        self._instance_info[InstanceInfoProcessor.ROI_PERCENT] += self._db_trade_performance.profit_percent

    def _process_total_capital(self):
        self._maybe_populate(InstanceInfoProcessor.TOTAL_CAPITAL, 0)
        self._instance_info[InstanceInfoProcessor.TOTAL_CAPITAL] += self._db_trade_performance.available_capital

    def _process_total_win_lose(self):
        self._maybe_populate(InstanceInfoProcessor.TOTAL_WINS, 0)
        self._maybe_populate(InstanceInfoProcessor.TOTAL_LOSSES, 0)
        self._maybe_populate(InstanceInfoProcessor.TOTAL_WINS_PERCENT, 0)
        self._maybe_populate(InstanceInfoProcessor.TOTAL_LOSSES_PERCENT, 0)

        profit = self._db_trade_performance.profit
        profit_percent = self._db_trade_performance.profit_percent
        if profit > 0:
            self._instance_info[InstanceInfoProcessor.TOTAL_WINS] += profit
            self._instance_info[InstanceInfoProcessor.TOTAL_WINS_PERCENT] += profit_percent

        if profit < 0:
            self._instance_info[InstanceInfoProcessor.TOTAL_LOSSES] += profit
            self._instance_info[InstanceInfoProcessor.TOTAL_LOSSES_PERCENT] += profit_percent

    def _process_profit_percents(self):
        self._maybe_populate(InstanceInfoProcessor.PROFIT_PERCENTS, [])
        self._instance_info[InstanceInfoProcessor.PROFIT_PERCENTS].append(self._db_trade_performance.profit_percent)

    def _process_fees(self):
        self._maybe_populate(InstanceInfoProcessor.TOTAL_FEES, 0)
        self._maybe_populate(InstanceInfoProcessor.MAX_FEE, 0)
        self._maybe_populate(InstanceInfoProcessor.TOTAL_TRADING_CAPITAL_FEE_PERCENTAGE, 0)
        self._maybe_populate(InstanceInfoProcessor.MAX_TRADING_CAPITAL_FEE_PERCENTAGE, 0)

        fee = self._db_trade_performance.fees
        self._instance_info[InstanceInfoProcessor.TOTAL_FEES] += fee
        if fee > self._instance_info[InstanceInfoProcessor.MAX_FEE]:
            self._instance_info[InstanceInfoProcessor.MAX_FEE] = fee

        trading_capital_fee = fee / self._db_trade_performance.available_capital
        self._instance_info[InstanceInfoProcessor.TOTAL_TRADING_CAPITAL_FEE_PERCENTAGE] += trading_capital_fee
        if trading_capital_fee > self._instance_info[InstanceInfoProcessor.MAX_TRADING_CAPITAL_FEE_PERCENTAGE]:
            self._instance_info[InstanceInfoProcessor.MAX_TRADING_CAPITAL_FEE_PERCENTAGE] = trading_capital_fee

    def _maybe_populate(self, key: str, value: any):
        if key not in self._instance_info:
            self._instance_info[key] = value

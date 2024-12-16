import datetime

import numpy as np
import consts
from mirage.database.mongo.common_operations import get_records
from mirage.performance.mirage_performance import DbTradePerformance
from mirage.performance.summary_report.instance_info_processor import InstanceInfoProcessor
from mirage.utils.date_utils import iso_string_to_datetime


class SummaryReportGenerator:
    STRATEGY = 'Strategy'
    INSTANCE = 'Instance'
    DATE_FROM = 'Date From'
    DATE_TO = 'Date To'
    RECORDS_COUNT = 'Records Count'
    PNL = 'PnL'
    AVG_PNL = 'Avg PnL'
    BATTING_AVG = 'Batting Avg'
    AVG_WIN = 'Avg Win'
    AVG_LOSS = 'Avg Loss'
    AVG_WIN_PERCENT = 'Avg Win Percent'
    AVG_LOSS_PERCENT = 'Avg Loss Percent'
    WIN_LOSS_RATIO = 'Win/Loss Ratio'
    SHARPE_RATIO = 'Sharpe Ratio'
    STANDARD_DEVIATION = 'Standard Deviation'
    AVG_ROI = 'Avg ROI'
    MAX_LOSS = 'Max Loss'
    MAX_PROFIT = 'Max Profit'
    MAX_LOSS_PERCENT = 'Max Loss Percent'
    MAX_PROFIT_PERCENT = 'Max Profit Percent'
    AVG_CAPITAL = 'Avg Capital'

    async def generate_report(self, date_from: str, date_to: str) -> list[dict[str, any]]:
        iso_date_from = iso_string_to_datetime(date_from) if date_from else None
        iso_date_to = iso_string_to_datetime(date_to) if date_to else None

        records = get_records(
            consts.DB_NAME_MIRAGE_PERFORMANCE, consts.COLLECTION_TRADE_OUTCOMES,
            self._build_query(iso_date_from, iso_date_to)
        )
        performance_summary = self._create_totals_summary(records)
        return self._generate_results(performance_summary, iso_date_from, iso_date_to)

    def _build_query(self, date_from: datetime.datetime, date_to: datetime.datetime) -> dict[str, any]:
        query = {}
        if date_from is not None:
            query[consts.RECORD_KEY_CREATED_AT] = {'$gte': date_from}

        if date_to is not None:
            if consts.RECORD_KEY_CREATED_AT not in query:
                query[consts.RECORD_KEY_CREATED_AT] = {}

            query[consts.RECORD_KEY_CREATED_AT]['$lte'] = date_to

        return query

    def _create_totals_summary(self, records) -> dict[str, any]:
        performance_summary = {}
        for record in records:
            db_trade_performance = DbTradePerformance(**record)
            if db_trade_performance.strategy_name not in performance_summary:
                performance_summary[db_trade_performance.strategy_name] = {}

            strategy_info = performance_summary[db_trade_performance.strategy_name]
            if db_trade_performance.strategy_instance not in strategy_info:
                strategy_info[db_trade_performance.strategy_instance] = {}

            InstanceInfoProcessor(strategy_info[db_trade_performance.strategy_instance], db_trade_performance).process()

        return performance_summary

    def _generate_results(self, perfs: dict[str, any], date_from: datetime.datetime, date_to: datetime.datetime) -> list[dict[str, any]]:
        results = []

        for strategy in perfs:
            strategy_data = perfs[strategy]
            for instance in strategy_data:
                result = {}
                data = strategy_data[instance]

                result[SummaryReportGenerator.STRATEGY] = strategy
                result[SummaryReportGenerator.INSTANCE] = instance
                result[SummaryReportGenerator.DATE_FROM] = date_from
                result[SummaryReportGenerator.DATE_TO] = date_to

                records_count = data[InstanceInfoProcessor.RECORDS_COUNT]
                result[SummaryReportGenerator.RECORDS_COUNT] = records_count

                pnl = data[InstanceInfoProcessor.PNL]
                result[SummaryReportGenerator.PNL] = pnl
                result[SummaryReportGenerator.AVG_PNL] = pnl / records_count

                winning_trades = data[InstanceInfoProcessor.WINNING_TRADES]
                result[SummaryReportGenerator.BATTING_AVG] = str((winning_trades / records_count) * 100) + '%'

                avg_win = data[InstanceInfoProcessor.TOTAL_WINS] / records_count
                avg_loss = data[InstanceInfoProcessor.TOTAL_LOSSES] / records_count
                result[SummaryReportGenerator.AVG_WIN] = avg_win
                result[SummaryReportGenerator.AVG_LOSS] = avg_loss
                result[SummaryReportGenerator.WIN_LOSS_RATIO] = (avg_win / abs(avg_loss)) if abs(avg_loss) > 0 else '-'

                losing_trades = records_count - winning_trades
                result[SummaryReportGenerator.AVG_WIN_PERCENT] = str((data[InstanceInfoProcessor.TOTAL_WINS_PERCENT] / winning_trades) * 100) + \
                    '%' if winning_trades > 0 else '-'
                result[SummaryReportGenerator.AVG_LOSS_PERCENT] = str((data[InstanceInfoProcessor.TOTAL_LOSSES_PERCENT] / losing_trades) * 100) + \
                    '%' if losing_trades > 0 else '-'

                result[SummaryReportGenerator.AVG_ROI] = str((data[InstanceInfoProcessor.ROI_PERCENT] / records_count) * 100) + '%'
                result[SummaryReportGenerator.MAX_LOSS] = data[InstanceInfoProcessor.MAX_LOSS]
                result[SummaryReportGenerator.MAX_PROFIT] = data[InstanceInfoProcessor.MAX_PROFIT]
                result[SummaryReportGenerator.MAX_LOSS_PERCENT] = str(data[InstanceInfoProcessor.MAX_LOSS_PERCENT] * 100) + '%'
                result[SummaryReportGenerator.MAX_PROFIT_PERCENT] = str(data[InstanceInfoProcessor.MAX_PROFIT_PERCENT] * 100) + '%'

                result[SummaryReportGenerator.AVG_CAPITAL] = data[InstanceInfoProcessor.TOTAL_CAPITAL] / records_count

                mean_return = np.mean(data[InstanceInfoProcessor.PROFIT_PERCENTS])
                std_dev_return = np.std(data[InstanceInfoProcessor.PROFIT_PERCENTS])
                sharpe_ratio = (mean_return / std_dev_return * np.sqrt(365)) if std_dev_return > 0 else '-'

                result[SummaryReportGenerator.STANDARD_DEVIATION] = str(std_dev_return * 100) + '%'
                result[SummaryReportGenerator.SHARPE_RATIO] = sharpe_ratio

                results.append(result)

        return results

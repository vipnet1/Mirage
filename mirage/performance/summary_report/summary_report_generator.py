import datetime
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
    WIN_LOSS_RATIO = 'Win/Loss Ratio'
    SHARPE_RATIO = 'Sharpe Ratio'
    AVG_ROI = 'Avg ROI'
    MAX_LOSS = 'Max Loss'
    MAX_PROFIT = 'Max Profit'
    MAX_LOSS_PERCENT = 'Max Loss Percent'
    MAX_PROFIT_PERCENT = 'Max Profit Percent'

    async def generate_report(self, date_from: str, date_to: str) -> list[dict[str, any]]:
        records = get_records(
            consts.DB_NAME_MIRAGE_PERFORMANCE, consts.COLLECTION_TRADE_OUTCOMES,
            self._build_query(
                iso_string_to_datetime(date_from) if date_from else None,
                iso_string_to_datetime(date_to) if date_to else None
            )
        )
        performance_summary = self._create_totals_summary(records)
        return self._generate_results(performance_summary, date_from, date_to)

    def _build_query(self, date_from: datetime.datetime, date_to: datetime.datetime) -> dict[str, any]:
        query = {}
        if date_from is not None:
            query[consts.RECORD_KEY_CREATED_AT] = {consts.RECORD_KEY_CREATED_AT: {'$gte': date_from}}

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

    def _generate_results(self, performance_summary: dict[str, any], date_from: str, date_to: str) -> list[dict[str, any]]:
        results = []

        for strategy in performance_summary:
            strategy_data = performance_summary[strategy]
            for instance in strategy_data:
                result = {}
                data = strategy_data[instance]

                result[SummaryReportGenerator.STRATEGY] = strategy
                result[SummaryReportGenerator.INSTANCE] = instance
                result[SummaryReportGenerator.DATE_FROM] = date_from if date_from else 'ALL'
                result[SummaryReportGenerator.DATE_TO] = date_to if date_to else 'ALL'

                records_count = data[InstanceInfoProcessor.RECORDS_COUNT]
                result[SummaryReportGenerator.RECORDS_COUNT] = records_count

                pnl = data[InstanceInfoProcessor.PNL]
                result[SummaryReportGenerator.PNL] = pnl
                result[SummaryReportGenerator.AVG_PNL] = pnl / records_count

                winning_trades = data[InstanceInfoProcessor.WINNING_TRADES]
                result[SummaryReportGenerator.BATTING_AVG] = str((winning_trades / records_count) * 100) + '%'
                result[SummaryReportGenerator.WIN_LOSS_RATIO] = winning_trades / (records_count - winning_trades)
                result[SummaryReportGenerator.SHARPE_RATIO] = ''
                result[SummaryReportGenerator.AVG_ROI] = str((data[InstanceInfoProcessor.ROI_PERCENT] / records_count) * 100) + '%'
                result[SummaryReportGenerator.MAX_LOSS] = data[InstanceInfoProcessor.MAX_LOSS]
                result[SummaryReportGenerator.MAX_PROFIT] = data[InstanceInfoProcessor.MAX_PROFIT]
                result[SummaryReportGenerator.MAX_LOSS_PERCENT] = str(data[InstanceInfoProcessor.MAX_LOSS_PERCENT] * 100) + '%'
                result[SummaryReportGenerator.MAX_PROFIT_PERCENT] = str(data[InstanceInfoProcessor.MAX_PROFIT_PERCENT] * 100) + '%'

                results.append(result)

        return results

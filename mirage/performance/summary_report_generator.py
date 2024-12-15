import datetime
import consts
from mirage.database.mongo.common_operations import get_records
from mirage.performance.mirage_performance import DbTradePerformance
from mirage.utils.date_utils import iso_string_to_datetime


class SummaryReportGenerator:
    STRATEGY = 'Strategy'
    INSTANCE = 'Instance'
    DATE_FROM = 'Date From'
    DATE_TO = 'Date To'
    INSTANCE = 'Date To'
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
        return []
        # performance_summary = self._create_totals_summary(records)
        # return self._generate_results(performance_summary)

    def _build_query(self, date_from: datetime.datetime, date_to: datetime.datetime) -> dict[str, any]:
        query = {consts.RECORD_KEY_CREATED_AT: {}}
        if date_from is not None:
            query[consts.RECORD_KEY_CREATED_AT]['$gte'] = date_from

        if date_to is not None:
            query[consts.RECORD_KEY_CREATED_AT]['$lte'] = date_to

        return query

    # def _create_totals_summary(self, records) -> dict[str, any]:
    #     performance_summary = {}
    #     for record in records:
    #         db_trade_performance = DbTradePerformance(**record)
    #         if db_trade_performance.strategy_name not in performance_summary:
    #             performance_summary[db_trade_performance.strategy_name] = {}

    #         strategy_info = performance_summary[db_trade_performance.strategy_name]
    #         if db_trade_performance.strategy_instance not in strategy_info:
    #             strategy_info[db_trade_performance.strategy_instance] = {}

    #         instance_info = strategy_info[db_trade_performance.strategy_instance]
    #         self._populate_instance_info(instance_info, db_trade_performance)

    #     return performance_summary

    # def _populate_instance_info(self, instance_info: dict[str, any], db_trade_performance: DbTradePerformance):
    #     if self.RECORDS_COUNT not in instance_info:
    #         instance_info[self.RECORDS_COUNT] = 0

    #     if self.TOTAL_PROFIT not in instance_info:
    #         instance_info[self.TOTAL_PROFIT] = 0

    #     if self.TOTAL_CAPITAL not in instance_info:
    #         instance_info[self.TOTAL_CAPITAL] = 0

    #     instance_info[self.RECORDS_COUNT] += 1
    #     instance_info[self.TOTAL_PROFIT] += db_trade_performance.profit
    #     instance_info[self.TOTAL_CAPITAL] += db_trade_performance.available_capital

    # def _generate_results(self, performance_summary: dict[str, any]) -> list[dict[str, any]]:
    #     results = []

    #     for strategy in performance_summary:
    #         strategy_data = performance_summary[strategy]
    #         for instance in strategy_data:
    #             data = strategy_data[instance]
    #             data[self.STRATEGY] = strategy
    #             data[self.INSTANCE] = instance
    #             self._populate_averages(data)
    #             results.append(data)

    #     return results

    # def _populate_averages(self, data: dict[str, any]) -> None:
    #     data[self.AVERAGE_PROFIT] = data[self.TOTAL_PROFIT] / data[self.RECORDS_COUNT]
    #     data[self.AVERAGE_PROFIT] = data[self.TOTAL_CAPITAL] / data[self.RECORDS_COUNT]

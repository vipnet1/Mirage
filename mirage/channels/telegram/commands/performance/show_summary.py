import csv
import os
import tempfile
import consts
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.database.mongo.common_operations import get_records
from mirage.performance.mirage_performance import DbTradePerformance


class PerformaceSummaryCommand(TelegramCommand):
    STRATEGY = 'strategy'
    INSTANCE = 'instance'
    RECORDS_COUNT = 'records_count'
    TOTAL_PROFIT = 'total_profit'
    TOTAL_CAPITAL = 'total_capital'
    AVERAGE_PROFIT = 'average_profit'
    AVERAGE_CAPITAL = 'average_capital'

    async def execute(self) -> None:
        records = get_records(consts.DB_NAME_MIRAGE_PERFORMANCE, consts.COLLECTION_TRADE_OUTCOMES, {})

        performance_summary = self._create_totals_summary(records)

        results_for_csv = self._generate_results_for_csv(performance_summary)
        await self._send_results_csv(results_for_csv)

    def _create_totals_summary(self, records) -> dict[str, any]:
        performance_summary = {}
        for record in records:
            db_trade_performance = DbTradePerformance(**record)
            if db_trade_performance.strategy_name not in performance_summary:
                performance_summary[db_trade_performance.strategy_name] = {}

            strategy_info = performance_summary[db_trade_performance.strategy_name]
            if db_trade_performance.strategy_instance not in strategy_info:
                strategy_info[db_trade_performance.strategy_instance] = {}

            instance_info = strategy_info[db_trade_performance.strategy_instance]
            self._populate_instance_info(instance_info, db_trade_performance)

        return performance_summary

    def _populate_instance_info(self, instance_info: dict[str, any], db_trade_performance: DbTradePerformance):
        if self.RECORDS_COUNT not in instance_info:
            instance_info[self.RECORDS_COUNT] = 0

        if self.TOTAL_PROFIT not in instance_info:
            instance_info[self.TOTAL_PROFIT] = 0

        if self.TOTAL_CAPITAL not in instance_info:
            instance_info[self.TOTAL_CAPITAL] = 0

        instance_info[self.RECORDS_COUNT] += 1
        instance_info[self.TOTAL_PROFIT] += db_trade_performance.profit
        instance_info[self.TOTAL_CAPITAL] += db_trade_performance.available_capital

    def _generate_results_for_csv(self, performance_summary: dict[str, any]) -> list[dict[str, any]]:
        results = []

        for strategy in performance_summary:
            strategy_data = performance_summary[strategy]
            for instance in strategy_data:
                data = strategy_data[instance]
                data[self.STRATEGY] = strategy
                data[self.INSTANCE] = instance
                self._populate_averages(data)
                results.append(data)

        return results

    def _populate_averages(self, data: dict[str, any]) -> None:
        data[self.AVERAGE_PROFIT] = data[self.TOTAL_PROFIT] / data[self.RECORDS_COUNT]
        data[self.AVERAGE_PROFIT] = data[self.TOTAL_CAPITAL] / data[self.RECORDS_COUNT]

    async def _send_results_csv(self, results_for_csv: list[dict[str, any]]) -> None:
        if not results_for_csv:
            await ChannelsManager.get_communication_channel().send_message('No trades to generate summary')
            return

        with tempfile.NamedTemporaryFile(mode='w', newline='', delete=False) as temp_file:
            writer = csv.DictWriter(temp_file, fieldnames=self._get_columns())
            writer.writeheader()
            writer.writerows(results_for_csv)
            filepath = temp_file.name

        await ChannelsManager.get_communication_channel().send_file(filepath, 'performance_summary.csv')
        os.remove(filepath)

    def _get_columns(self) -> list[str]:
        return [
            self.STRATEGY,
            self.INSTANCE,
            self.RECORDS_COUNT,
            self.AVERAGE_CAPITAL,
            self.AVERAGE_PROFIT,
            self.TOTAL_CAPITAL,
            self.TOTAL_PROFIT,
        ]

import csv
import os
import tempfile
from mirage.channels.channels_manager import ChannelsManager
from mirage.channels.telegram.exceptions import MirageTelegramException
from mirage.channels.telegram.telegram_command import TelegramCommand
from mirage.performance.summary_report.summary_report_generator import SummaryReportGenerator


class PerformaceSummaryCommand(TelegramCommand):
    DATE_ALL = 'ALL'

    async def execute(self) -> None:
        date_from = self._get_top_line()
        if not date_from:
            raise MirageTelegramException(f'Provide date from. For example 2024-02-15. For all time write {PerformaceSummaryCommand.DATE_ALL}.')

        self._remove_first_line()

        date_to = self._get_top_line()
        if not date_to:
            raise MirageTelegramException(f'Provide date to. For example 2024-02-15. For all time write {PerformaceSummaryCommand.DATE_ALL}.')

        self._remove_first_line()

        if date_from == PerformaceSummaryCommand.DATE_ALL:
            date_from = ''

        if date_to == PerformaceSummaryCommand.DATE_ALL:
            date_to = ''

        results_for_csv = await SummaryReportGenerator().generate_report(date_from, date_to)
        await self._send_results_csv(results_for_csv)

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

    # The order here is the one will be in the file
    def _get_columns(self) -> list[str]:
        return [
            SummaryReportGenerator.STRATEGY,
            SummaryReportGenerator.INSTANCE,
            SummaryReportGenerator.DATE_FROM,
            SummaryReportGenerator.DATE_TO,
            SummaryReportGenerator.RECORDS_COUNT,
            SummaryReportGenerator.PNL,
            SummaryReportGenerator.AVG_PNL,
            SummaryReportGenerator.BATTING_AVG,
            SummaryReportGenerator.WIN_LOSS_RATIO,
            SummaryReportGenerator.SHARPE_RATIO,
            SummaryReportGenerator.STANDARD_DEVIATION,
            SummaryReportGenerator.AVG_ROI,
            SummaryReportGenerator.AVG_CAPITAL,
            SummaryReportGenerator.AVG_WIN,
            SummaryReportGenerator.AVG_WIN_PERCENT,
            SummaryReportGenerator.AVG_LOSS,
            SummaryReportGenerator.AVG_LOSS_PERCENT,
            SummaryReportGenerator.MAX_LOSS,
            SummaryReportGenerator.MAX_PROFIT,
            SummaryReportGenerator.MAX_LOSS_PERCENT,
            SummaryReportGenerator.MAX_PROFIT_PERCENT
        ]

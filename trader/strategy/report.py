from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal


# TODO：参考：
#  http://help.tradestation.com/09_01/tsportfolio/reports/about_performance_report.htm
#  https://www.investopedia.com/articles/fundamental-analysis/10/strategy-performance-reports.asp

@dataclass
class AllTradesReport:
    """
    全部交易报告
    """

    total_net_profit: Decimal  # 总净收益
    gross_profit: Decimal  # 总收益
    gross_lose: Decimal  # 总亏损
    profit_factor: float  # 利润系数（毛利除以整个交易期间的毛损[包括佣金]）TODO: property
    open_position_pnl: Decimal  # 开仓盈亏（数量）

    number_of_trades: int  # 交易次数
    number_of_winning_trades: int  # 盈利次数
    number_of_losing_trades: int  # 亏损次数
    percent_profitable: float  # 盈亏百分比

    largest_winning_trade: Decimal  # 最大盈利（数量）
    largest_losing_trade: Decimal  # 最大亏损（数量）
    avg_winning_trade: Decimal  # 平均盈利（数量）
    avg_losing_trade: Decimal  # 平均亏损（数量）
    avg_trade: Decimal  # 平均盈亏，win+lose（数量）
    avg_winning_avg_loss_ratio: float  # 平均盈利/亏损比

    max_consecutive_winners: int  # 最大连续盈利次数
    max_consecutive_losers: int  # 最大连续亏损次数
    avg_number_of_bars_in_winners: int  # 平均盈利周期
    avg_number_of_bars_in_losers: int  # 平均亏损周期

    max_bar_draw_down: Decimal  # 最大周期内跌幅（数量）# TODO: 最大周期内回撤百分比
    max_draw_down: Decimal  # 最大回撤 # TODO: 最大回撤百分比

    max_number_of_contracts_held: int  # 最大持有合约数

    account_size_required: Decimal  # （需要的）账户规模
    return_of_account: float  # 账户收益百分比（return on initial capital）
    annual_rate_of_return: float  # 年化收益率

    return_retracement_ratio: float  # 回报率（RRR） –表示平均年化复合回报率R除以平均最大回报率AMR度量值。存款准备金= R / AMR
    rina_index: float  # 瑞纳指数

    max_equity_run_up: Decimal  # 最大权益增长（从最低权益提高到最高的利润积累）

    trading_period: timedelta  # 交易周期
    percent_of_time_in_the_market: float  # 在市场中的时间


@dataclass
class LongTradesReport:
    """
    做多交易报告
    """


@dataclass
class ShortTradesReport:
    """
    做空交易报告
    """


@dataclass
class StrategyPerformanceReport:
    """
    TODO：策略报告
    """
    begin: datetime  # 起始时间
    end: datetime  # 结束时间
    strategy_name: str  # 策略名称
    base_currency: str  # 本位币
    all_trades: AllTradesReport  # 全部交易的报告
    long_trades: LongTradesReport  # 做多交易的报告
    short_trades: ShortTradesReport  # 做空交易的报告


class ReportGenerator(ABC):
    @abstractmethod
    def generate(self) -> StrategyPerformanceReport:
        """
        产生策略报告

        Returns:
            策略报告
        """

from dataclasses import dataclass
from decimal import Decimal, MAX_EMAX

from trader.spot.api.spot_api import SpotApi
from trader.spot.types import CoinPair
from trader.spot.types.kline import KlinePeriod


@dataclass
class BarSummary:
    coin_pair: CoinPair  # 币对
    period: KlinePeriod  # K线周期

    low_avg_price: Decimal  # 最小平均价格
    high_avg_price: Decimal  # 最大平均价格

    avg_avg_price: Decimal  # 平均价格
    avg_price_gap: Decimal  # 平均价差
    avg_price_path: Decimal  # 平均价格最小变化路径
    avg_gap_price_ratio: Decimal  # 平均 价差/均价 比率
    avg_path_price_ratio: Decimal  # 平均 价格路径/均价 比率

    @property
    def avg_price_ratio(self) -> float:
        """
        当前价格在最低、最高价中的比例

        0: 最低价
        1: 最高价
        0.3: 最低价到最高价 30% 的价位

        Returns:
            当前价离历史最低、最高价的比例
        """
        return float((self.avg_avg_price - self.low_avg_price) / (self.high_avg_price - self.low_avg_price))

    def __str__(self):
        return f"{self.coin_pair}, {self.period.name}, 均价: {self.avg_avg_price:0.8f}, " \
               f"价格偏离比率: {self.avg_price_ratio:0.6f}, " \
               f"最小平均价格: {self.low_avg_price}, 最大平均价格: {self.high_avg_price}, " \
               f"价差: {self.avg_price_gap}, 价格路径: {self.avg_price_path}, " \
               f"价差/均价比: {self.avg_gap_price_ratio:0.8f}, 价格路径/均价比: {self.avg_path_price_ratio:0.8f}"


class KlineAnalysis:
    def __init__(self, api: SpotApi):
        self.api = api

    def calculate(self, coin_pair, period=KlinePeriod.HOUR1) -> BarSummary:
        bars = self.api.get_kline(coin_pair=coin_pair, period=period)
        total_avg_price = Decimal()
        total_price_gap = Decimal()
        total_price_path = Decimal()
        total_gap_price_ratio = Decimal()
        total_path_price_ratio = Decimal()

        low_avg_price = Decimal(MAX_EMAX)
        high_avg_price = Decimal()
        for bar in bars:
            total_avg_price += bar.avg_price
            total_price_gap += bar.price_gap
            total_price_path += bar.price_path
            total_gap_price_ratio += bar.gap_price_ratio
            total_path_price_ratio += bar.path_price_ratio
            high_avg_price = max(bar.avg_price, high_avg_price)
            low_avg_price = min(bar.avg_price, low_avg_price)

        return BarSummary(
            coin_pair=coin_pair,
            period=period,
            low_avg_price=low_avg_price,
            high_avg_price=high_avg_price,
            avg_avg_price=total_avg_price / len(bars),
            avg_price_gap=total_price_gap / len(bars),
            avg_price_path=total_price_path / len(bars),
            avg_gap_price_ratio=total_gap_price_ratio / len(bars),
            avg_path_price_ratio=total_path_price_ratio / len(bars),
        )

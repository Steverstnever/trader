from dataclasses import dataclass
from decimal import Decimal

from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.types import CoinPair
from trader.spot.types.kline import KlinePeriod


@dataclass
class BarSummary:
    coin_pair: CoinPair  # 币对
    period: KlinePeriod  # K线周期
    avg_avg_price: Decimal  # 平均价格
    avg_price_gap: Decimal  # 平均价差
    avg_price_path: Decimal  # 平均价格最小变化路径
    avg_gap_price_ratio: Decimal  # 平均 价差/平均价格 比率
    avg_path_price_ratio: Decimal  # 平均 价格路径/平均价格 比率


class CoinPairBarPerformance:
    def __init__(self, ):
        self.api = BinanceSpotApi()

    def calculate(self, coin_pair, period=KlinePeriod.HOUR1) -> BarSummary:
        bars = self.api.get_kline(coin_pair=coin_pair, period=period)
        total_avg_price = Decimal()
        total_price_gap = Decimal()
        total_price_path = Decimal()
        total_gap_price_ratio = Decimal()
        total_path_price_ratio = Decimal()
        for bar in bars:
            total_avg_price += bar.avg_price
            total_price_gap += bar.price_gap
            total_price_path += bar.price_path
            total_gap_price_ratio += bar.gap_price_ratio
            total_path_price_ratio += bar.path_price_ratio

        return BarSummary(
            avg_avg_price=total_avg_price / len(bars),
            avg_price_gap=total_price_gap / len(bars),
            avg_price_path=total_price_path / len(bars),
            avg_gap_price_ratio=total_gap_price_ratio / len(bars),
            avg_path_price_ratio=total_path_price_ratio / len(bars),
        )


summary = CoinPairBarPerformance().calculate(coin_pair=CoinPair('BNB', 'USDT'), period=KlinePeriod.HOUR1)
print(f"{summary}")

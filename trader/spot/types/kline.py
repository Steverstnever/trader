from dataclasses import dataclass
from datetime import timedelta, datetime
from decimal import Decimal
from enum import Enum

from trader.utils import normalize_decimal


class KlinePeriod(Enum):
    MIN1 = timedelta(minutes=1)
    MIN5 = timedelta(minutes=5)
    MIN15 = timedelta(minutes=15)
    MIN30 = timedelta(minutes=30)
    HOUR1 = timedelta(hours=1)
    HOUR4 = timedelta(hours=4)
    HOUR8 = timedelta(hours=8)
    DAY1 = timedelta(days=1)
    WEEK1 = timedelta(weeks=1)


@dataclass
class Bar:
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @property
    def avg_price(self):
        return normalize_decimal((self.high + self.low + self.close) / 3)

    @property
    def is_up(self):
        return self.close > self.open

    @property
    def price_gap(self):
        return self.high - self.low

    @property
    def price_path(self):
        """
        最小价格路径总和

        min（
            开盘 -> 最高 -> 最低 -> 收盘，
            开盘 -> 最低 -> 最高 -> 收盘
            ）

        价格在一个 bar 内最少通过的价格路径

        Returns:
            价格在一个 bar 内最少通过的价格路径
        """
        return min((self.high - self.open) + (self.high - self.low) + (self.close - self.low),
                   (self.open - self.low) + (self.high - self.low) + (self.high - self.close))

    @property
    def gap_price_ratio(self):
        return normalize_decimal(self.price_gap / self.avg_price)

    @property
    def path_price_ratio(self):
        return normalize_decimal(self.price_path / self.avg_price)

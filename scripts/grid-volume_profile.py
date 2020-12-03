# 根据 K 线自动计算网格
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import List

number_of_levels = 30  # 格线数量
min_price_gap_pct = 0.005  # 最小价格间隔百分比（小于这个间隔就没有盈利）
min_price_size = Decimal("0.001")


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
        result = (self.high + self.low + self.close) / 3
        return result.quantize(min_price_size, ROUND_DOWN)


bars: List[Bar] = []
price_dict = {}
for price, volume in [(bar.avg_price, bar.volume) for bar in bars]:
    if price in price_dict:
        price_dict[price] = price_dict[price] + volume  # 把相同的价格归并
    else:
        price_dict[price] = volume
sorted(price_dict)

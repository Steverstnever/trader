from dataclasses import dataclass
from decimal import Decimal

from .coin_pair import CoinPair


@dataclass
class BookTicker:
    coin_pair: CoinPair  # 币对   # TODO: 此字段可以不要
    ask1_price: Decimal  # 最佳卖价一
    ask1_qty: Decimal  # 最佳卖价一数量
    bid1_price: Decimal  # 最佳买价一
    bid1_qty: Decimal  # 最佳买价一数量

    @property
    def price_gap(self):
        """
        价差（卖价1-买价1）
        """
        return self.ask1_price - self.bid1_price

    @property
    def avg_price(self):
        """
        买卖（算术平均）均价
        """
        return (self.ask1_price + self.bid1_price) / 2

    @property
    def avg_price_qty_weighted(self):
        """
        买卖（数量加权）均价
        """
        total_qty = self.ask1_qty + self.bid1_qty
        if total_qty == Decimal(0):
            return self.ask1_price
        else:
            return self.bid1_price + self.ask1_qty / total_qty * self.price_gap

    @property
    def compact_display_str(self) -> str:
        """
        紧凑形式展示，用于日志输出等

        Returns:
            紧凑形式展示的字符串
        """
        return f"{self.coin_pair.symbol}, ask1={str(self.ask1_price)}, ask1_qty={str(self.ask1_qty)}" \
               f", bid1={str(self.bid1_price)}, bid1_qty={str(self.bid1_qty)}"

    def __str__(self):
        return self.compact_display_str

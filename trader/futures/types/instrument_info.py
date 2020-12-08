from dataclasses import dataclass
from decimal import Decimal, MAX_EMAX, ROUND_DOWN

from .symbol import ContractPair


@dataclass
class FuturesInstrumentInfo:
    contract_pair: ContractPair  # 币对
    min_price_size: Decimal  # 价格精度
    min_qty_size: Decimal  # 数量精度

    max_price: Decimal = Decimal(MAX_EMAX)  # 最大价格
    min_price: Decimal = Decimal(0)  # 最小价格

    max_qty: Decimal = Decimal(MAX_EMAX)  # 最大数量
    min_qty: Decimal = Decimal(0)  # 最小数量

    min_notional: Decimal = Decimal(0)  # 最小名义价格（下单时的：price*qty）

    def quantize_price(self, price: Decimal) -> Decimal:
        """
        根据精度裁剪价格

        Args:
            price (Decimal): 价格，比如：18773.12356789

        Returns:
            裁剪后的结果，比如：精度为 0.001 时，裁剪的结果为 19773.123
        """
        return price.quantize(self.min_price_size, rounding=ROUND_DOWN)

    def quantize_qty(self, qty: Decimal) -> Decimal:
        """
        根据精度裁剪数量

        Args:
            qty (Decimal): 数量, 比如: 1003.12356789

        Returns:
            裁剪后的结果，比如：精度为 0.001 时的结果是 1003.123
        """
        return qty.quantize(self.min_qty_size, rounding=ROUND_DOWN)

    def is_valid_price(self, price: Decimal) -> bool:
        """
        判断指定的价格是否合法

        Args:
            price (Decimal): 价格

        Returns:
            true 合法
        """
        return self.min_price <= price < self.max_price and (price - self.min_price) % self.min_price_size == 0

    def is_valid_qty(self, qty: Decimal) -> bool:
        """
        判断指定的数量是否合法

        Args:
            qty (Decimal): 数量

        Returns:
            true 合法
        """
        return self.min_qty <= qty < self.max_qty and (qty - self.min_qty) % self.min_qty_size == 0

    def is_valid_notional(self, price: Decimal, qty: Decimal):
        """
        判断是否合法的名义价格（price*qty）
        Args:
            price (Decimal): 价格
            qty (qty): 数量

        Returns:
            true 合法的名义价格
        """
        return self.is_valid_price(price) and self.is_valid_qty(qty) and price * qty >= self.min_notional

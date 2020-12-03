from abc import ABC, abstractmethod
from decimal import Decimal

from trader.spot.types import OrderSide, CoinPair
from trader.spot.types.order_types import Order


class OrderExecutor(ABC):

    @abstractmethod
    def _place_order(self, coin_pair: CoinPair, order_side: OrderSide, price: Decimal, qty: Decimal) -> Order:
        """
        下订单

        Args:
            coin_pair (CoinPair): 币对
            order_side (OrderSide): 买卖方向
            price (Decimal): 价格
            qty (Decimal): 数量
        Returns:
            下单
        """

    def buy(self, coin_pair: CoinPair, price: Decimal, qty: Decimal) -> Order:
        """
        按照指定价格买入资产

        Args:
            coin_pair (CoinPair): 币对
            price (Decimal): 资产价格
            qty (Decimal): 资产数量

        Returns:
            订单结果
        """
        # assert self.is_valid_price(price)
        # assert self.is_valid_qty(qty)
        return self._place_order(coin_pair=coin_pair, order_side=OrderSide.BUY, price=price, qty=qty)

    def sell(self, coin_pair: CoinPair, price: Decimal, qty: Decimal) -> Order:
        """
        按照指定价格卖出资产

        Args:
            coin_pair (CoinPair): 币对
            price (Decimal): 资产价格
            qty (Decimal): 资产数量

        Returns:
            订单结果
        """
        # assert self.is_valid_price(price)
        # assert self.is_valid_qty(qty)
        # return self.adapter.sell(self.coin_pair, price, qty)
        return self._place_order(coin_pair=coin_pair, order_side=OrderSide.SELL, price=price, qty=qty)


class OrderExecutorProvider(ABC):
    """
    订单执行提供器
    """

    @abstractmethod
    def get_order_executor(self) -> OrderExecutor:
        """
        获取订单执行器

        Returns:
            订单执行器
        """

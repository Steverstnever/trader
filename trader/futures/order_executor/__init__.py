from abc import ABC, abstractmethod
from decimal import Decimal

from trader.futures.types import OrderSide, ContractPair, PositionSide
from trader.spot.types.order_types import Order


class OrderExecutor(ABC):

    @abstractmethod
    def _place_order(self, contract_pair: ContractPair,
                     order_side: OrderSide, contract_type: PositionSide, price: Decimal,
                     stop_price: Decimal, qty: Decimal, **kwargs) -> Order:
        """"""

    def short(self, contract_pair: ContractPair, price: Decimal, qty: Decimal, **kwargs) -> Order:
        """做空"""
        return self._place_order(contract_pair, OrderSide.SELL, PositionSide.SHORT, price, qty, **kwargs)

    def buy(self, contract_pair: ContractPair, price: Decimal, qty: Decimal, **kwargs):
        """做多"""
        return self._place_order(contract_pair, OrderSide.BUY, PositionSide.SHORT, price, qty, **kwargs)

    def sell(self, contract_pair: ContractPair, price, qty, **kwargs):
        """平多"""
        return self._place_order(contract_pair, OrderSide.SELL, PositionSide.LONG, price, qty, **kwargs)

    def cover(self, contract_pair: ContractPair, price, qty, **kwargs):
        """平空"""
        return self._place_order(contract_pair, OrderSide.BUY, PositionSide.SHORT, contract_pair, price, qty, **kwargs)


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

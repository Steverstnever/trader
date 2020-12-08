from abc import ABC, abstractmethod
from decimal import Decimal

from trader.futures.types import OrderSide, ContractPair, PositionSide
from trader.spot.types.order_types import Order


class OrderExecutor(ABC):

    @abstractmethod
    def _place_order(self, client_order_id: str, contract_pair: ContractPair,
                     order_side: OrderSide, contract_type: PositionSide, price: Decimal,
                     stop_price: Decimal, qty: Decimal) -> Order:
        """"""

    def buy(self, contract_pair: ContractPair, price: Decimal, qty: Decimal) -> Order:

        return self._place_order(contract_pair=contract_pair, order_side=OrderSide.BUY, price=price, qty=qty)

    def sell(self, contract_pair: ContractPair, price: Decimal, qty: Decimal) -> Order:
        return self._place_order(contract_pair=contract_pair, order_side=OrderSide.SELL, price=price, qty=qty)


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

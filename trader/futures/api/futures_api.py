from abc import ABCMeta, abstractmethod
from decimal import Decimal

from trader.futures.types import ContractPair
from trader.futures.types.order_types import OrderSide, PositionSide, TimeInForce


class FuturesApi(metaclass=ABCMeta):

    @abstractmethod
    def klines(self, contract_pair: ContractPair, interval: str, **kwargs):
        """"""

    @abstractmethod
    def create_stop_order(self,
                          client_order_id: str,
                          contract_pair: ContractPair,
                          order_side: OrderSide,
                          position_side: PositionSide,
                          price: Decimal,
                          stop_price: Decimal,
                          qty: Decimal,
                          tif: TimeInForce,
                          **kwargs):
        """"""

    @abstractmethod
    def delete_all_order(self, contract_pair: ContractPair, **kwargs):
        """"""

    @abstractmethod
    def available_balance(self, symbol: str) -> Decimal:
        """"""

    @abstractmethod
    def get_position(self, contract_pair: ContractPair):
        """"""

    @abstractmethod
    def query_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str):
        """"""

    @abstractmethod
    def cancel_order(self, contract_pair: ContractPair, client_order_id: str, order_id: str):
        """"""

    @abstractmethod
    def get_instrument_info(self, contract_pair: ContractPair):
        """"""

    @abstractmethod
    def cancel_all(self, contract_pair: ContractPair):
        """"""

    @abstractmethod
    def get_balance_by_symbol(self, asset_symbol: str) -> Decimal:
        """"""

    @abstractmethod
    def gen_client_order_id(self):
        """"""

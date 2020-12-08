from abc import ABC, abstractmethod

from trader.futures.types import ContractPair


class TradeProvider(ABC):

    @abstractmethod
    def cancel_all_orders(self, contract_pair: ContractPair):
        """ 取消所有订单 """

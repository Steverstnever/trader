from abc import ABC, abstractmethod

from trader.futures.types import ContractPair
from trader.futures.types import FuturesInstrumentInfo


class InstrumentInfoProvider(ABC):
    """
    商品信息提供器
    """

    @abstractmethod
    def get_instrument_info(self, contract_pair: ContractPair) -> FuturesInstrumentInfo:
        """
        交易商品信息提供器

        Args:
            contract_pair (ContractPair): 币对

        Returns:
            交易商品信息
        """

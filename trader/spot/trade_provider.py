from abc import ABC, abstractmethod
from typing import List

from trader.spot.types import CoinPair, Trade


class TradeProvider(ABC):

    @abstractmethod
    def cancel_all_orders(self, coin_pair: CoinPair):
        """
        取消所有订单

        Args:
            coin_pair (CoinPair): 币对
        """

    @abstractmethod
    def get_trades(self, coin_pair: CoinPair, trade_id: str = None) -> List[Trade]:
        """
        获取成交记录列表

        Args:
            coin_pair (CoinPair): 币对
            trade_id (str): 获取指定成交记录 id 以后的成交记录

        Returns:
            成交记录列表
        """

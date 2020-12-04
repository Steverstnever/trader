from abc import ABC, abstractmethod
from typing import List

from trader.spot.types import CoinPair
from trader.spot.types.book_ticker import BookTicker
from trader.spot.types.instrument_info import SpotInstrumentInfo
from trader.spot.types.kline import KlinePeriod, Bar


class BookTickerProvider(ABC):
    """
    最优挂单提供器
    """

    @abstractmethod
    def get_book_ticker(self, coin_pair: CoinPair) -> BookTicker:
        """
        返回当前最优的挂单(最高买单，最低卖单)

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            最优挂单
        """


class InstrumentInfoProvider(ABC):
    """
    商品信息提供器
    """

    @abstractmethod
    def get_instrument_info(self, coin_pair: CoinPair) -> SpotInstrumentInfo:
        """
        交易商品信息提供器

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            交易商品信息
        """


class KlineProvider(ABC):
    """
    K线提供器
    """

    @abstractmethod
    def get_kline(self, coin_pair: CoinPair, period: KlinePeriod) -> List[Bar]:
        """
        获取K线
        Args:
            coin_pair (CoinPair): 币对
            period (KlinePeriod): K线周期

        Returns:
            K线列表
        """

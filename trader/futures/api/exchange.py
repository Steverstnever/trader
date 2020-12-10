from dataclasses import dataclass
from enum import Enum
from typing import Type

from trader.credentials import Credentials
from trader.futures.api.binance_futures_api import BinanceCoinFuturesApi, BinanceUSDTFuturesApi


@dataclass
class ApiInfo:
    usdt_futures_api_class: Type[BinanceUSDTFuturesApi]
    coin_futures_api_class: Type[BinanceCoinFuturesApi]


class Exchange(Enum):
    """
    现货 API 提供者
    """
    BINANCE = ApiInfo(usdt_futures_api_class=BinanceUSDTFuturesApi, coin_futures_api_class=BinanceCoinFuturesApi)
    HUOBI = None
    OKEX = None

    def create_usdt_future_api(self, credentials: Credentials):
        return self.value.usdt_futures_api_class(credentials)

    def create_coin_future_api(self, credentials: Credentials):
        return self.value.coin_futures_api_class(credentials)


exchange_map = {
    'binance': Exchange.BINANCE,
    'huobi': Exchange.HUOBI,
    'okex': Exchange.OKEX
}

from dataclasses import dataclass
from enum import Enum
from typing import Type

from trader.credentials import Credentials
from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.api.spot_api import SpotApi


@dataclass
class ApiInfo:
    spot_api_class: Type[SpotApi]


class Exchange(Enum):
    """
    现货 API 提供者
    """
    BINANCE = ApiInfo(spot_api_class=BinanceSpotApi)
    HUOBI = None
    OKEX = None

    def create_spot_api(self, credentials: Credentials):
        return self.value.spot_api_class(credentials)

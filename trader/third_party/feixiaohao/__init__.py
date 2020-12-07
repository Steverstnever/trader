import typing
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

import requests


@dataclass
class CoinInfo:
    """
    加密货币信息类
    """
    id: str
    name: str
    symbol: str
    rank: int
    logo: str
    logo_png: str
    price_usd: Decimal
    price_btc: Decimal
    volume_24h_usd: Decimal
    market_cap_usd: Decimal
    available_supply: Decimal
    total_supply: Decimal
    max_supply: Decimal
    percent_change_1h: Decimal
    percent_change_24h: Decimal
    percent_change_7d: Decimal
    last_updated: int
    last_datetime: datetime = field(init=False)

    def __post_init__(self):
        self.last_datetime = datetime.fromtimestamp(self.last_updated)


def get_top_coins(limit: int = 100) -> typing.List[CoinInfo]:
    """
    调用非小号 api，获取币种信息
    :param limit: 返回数量，缺省为 100个
    :return: 币种信息列表
    """

    params = {"limit": limit}
    raw_json = requests.get(f"https://fxhapi.feixiaohao.com/public/v1/ticker", params).json()
    # 返回数据格式如下：
    # {
    #     "id": "bitcoin",
    #     "name": "Bitcoin",
    #     "symbol": "BTC",
    #     "rank": 1,
    #     "logo": "https://s1.bqiapp.com/coin/20181030_72_webp/bitcoin_200_200.webp",
    #     "logo_png": "https://s1.bqiapp.com/coin/20181030_72_png/bitcoin_200_200.png",
    #     "price_usd": 5225,
    #     "price_btc": 1,
    #     "volume_24h_usd": 5150321567,
    #     "market_cap_usd": 92163602317,
    #     "available_supply": 17637575,
    #     "total_supply": 17637575,
    #     "max_supply": 21000000,
    #     "percent_change_1h": 0.21,
    #     "percent_change_24h": 0.64,
    #     "percent_change_7d": 6,
    #     "last_updated": 1554886833
    # }
    result = []
    for raw_kwargs in raw_json:
        coin_info = CoinInfo(**raw_kwargs)
        result.append(coin_info)
    return result

import logging
from pprint import pprint

from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.types import CoinPair
from trader.utils import load_dev_credentials

logging.basicConfig(level=logging.INFO)


credentials = load_dev_credentials()
api = BinanceSpotApi(credentials)

# TODO: 使用命令行参数传入币对

coin_pair = CoinPair("BUSD", "USDT")
orders = api.cancel_all(coin_pair)  # TODO：cancel all 或者 cancel 指定的订单
pprint(orders)

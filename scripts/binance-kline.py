from trader.third_party.feixiaohao import get_top_coins
from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.tools import KlineAnalysis
from trader.spot.types.kline import KlinePeriod

top_coins = [top_coin.symbol for top_coin in get_top_coins(20)]
print(top_coins)

api = BinanceSpotApi()
coin_pairs = api.get_products()
# print(coin_pairs)

top_coin_pairs = [coin_pair for coin_pair in coin_pairs
                  if coin_pair.asset_symbol in top_coins and coin_pair.asset_symbol in top_coins]

print(f"<< 开始分析 K线特征 ({len(top_coin_pairs)}) >>".center(80, '*'))
kline_analysis = KlineAnalysis(api)

items = []
for coin_pair in top_coin_pairs:
    summary = kline_analysis.calculate(coin_pair=coin_pair, period=KlinePeriod.HOUR4)
    items.append(summary)
    # print(f"{summary}")

items.sort(key=lambda item: item.avg_path_price_ratio, reverse=True)
for i, item in enumerate(items):
    print(f"{i} => {item}")

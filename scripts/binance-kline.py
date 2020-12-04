from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.tools import KlineAnalysis
from trader.spot.types.kline import KlinePeriod
from trader.third_party.feixiaohao import get_top_coins

top_coins = {top_coin.symbol for top_coin in get_top_coins(20)}
print(top_coins)

api = BinanceSpotApi()
coin_pairs = api.get_products()

top_coin_pairs = [coin_pair for coin_pair in coin_pairs
                  if coin_pair.asset_symbol in top_coins and coin_pair.cash_symbol in top_coins]

print(f"<< 开始分析 K线特征 ({len(top_coin_pairs)}) >>".center(80, '*'))
kline_analysis = KlineAnalysis(api)

summaries = [
    kline_analysis.calculate(coin_pair=coin_pair, period=KlinePeriod.WEEK1)
    for coin_pair in top_coin_pairs
]

summaries.sort(key=lambda item: item.avg_path_price_ratio, reverse=True)
for i, summary in enumerate(summaries):
    print(f"{i} => {summary}")

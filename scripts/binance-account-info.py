import logging

from trader.spot.api.binance_spot_api import BinanceSpotApi
from trader.spot.types import CoinPair
from trader.utils import load_dev_credentials

logging.basicConfig(level=logging.DEBUG)

credentials = load_dev_credentials()
print("<< 账户信息 >>".center(80, '*'))
print(f"当前账户: {credentials}")

api = BinanceSpotApi(credentials)

coin_pair = CoinPair("BNB", "USDT")  # TODO: 命令行
instrument_info = api.get_instrument_info(coin_pair)
# pprint(instrument_info)
# pprint(instrument_info.is_valid_qty(instrument_info.min_qty))
print(f"当前币对: {coin_pair}")
print()

print('<< 资产余额 >>'.center(80, '*'))
asset_free_amount, asset_locked_amount = api.get_balance_by_symbol(coin_pair.asset_symbol)
print(f"账户现货资产 {coin_pair.asset_symbol}: 余额 {asset_free_amount}, 冻结 {asset_locked_amount}")
cash_free_amount, cash_locked_amount = api.get_balance_by_symbol(coin_pair.cash_symbol)
print(f"账户现货现金 {coin_pair.cash_symbol}: 余额 {cash_free_amount}, 冻结 {cash_locked_amount}")
print()

print('<< 当前报价 >>'.center(80, '*'))
print(f"当前最优报价：{api.get_book_ticker(coin_pair)}")
print()

print('<< 最近订单 >>'.center(80, '*'))
print('TODO: ...')  # TODO:
print()

# pprint(api.get_trades(coin_pair))

# print('create limit order'.center(80, '-'))
# order: Order = api.create_limit_order(coin_pair, OrderSide.BUY, price=Decimal(10.0), qty=Decimal(1),
#                                       tif=TimeInForce.GTC)
# pprint(order)
# time.sleep(1.5)
#
# print('cancel order'.center(80, '-'))
# order = api.cancel_order(coin_pair, order.order_id)
# pprint(order)
#
# print('!' * 80)
#
# for i in range(10):
#     time.sleep(1.5)
#     print('query order'.center(80, '-'))
#     order = api.query_order(coin_pair, order.order_id)
#     pprint(order)
#
print("<< 最近成交 >>".center(80, '*'))
trades = api.get_trades(coin_pair)
for t in trades:
    print(t)

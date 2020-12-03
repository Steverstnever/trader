from decimal import Decimal

from trader.spot.types import CoinPair, OrderSide
from trader.spot.types.instrument_info import SpotInstrumentInfo


def test_coin_pair():
    cp = CoinPair('btc', 'usdt')
    assert cp.symbol == 'btc$$usdt'


def test_market_info():
    smi = SpotInstrumentInfo(min_price_size=Decimal("0.001"), min_qty_size=Decimal("0.1"))
    assert smi.quantize_qty(Decimal("12345.67890")) == Decimal("12345.6")
    assert smi.quantize_price(Decimal("12345.67890")) == Decimal("12345.678")


def test_order_side_from_str():
    assert OrderSide['BUY'] == OrderSide.BUY

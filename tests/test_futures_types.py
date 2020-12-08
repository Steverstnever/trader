from datetime import date

from trader.futures.types import FuturesContact
from trader.spot.types import CoinPair


def test_futures_contract():
    fc = FuturesContact(CoinPair('BTC', 'USD'), delivery_date=date(2020, 3, 26))
    assert fc.symbol == 'BTC$USD@200326'

    fc = FuturesContact.from_symbol(fc.symbol)
    assert fc.underlying_asset.symbol == 'BTC$USD'
    assert fc.delivery_date == date(2020, 3, 26)

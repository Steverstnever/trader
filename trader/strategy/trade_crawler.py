from trader.spot.trade_provider import TradeProvider
from trader.spot.types import CoinPair
from trader.store import StrategyStore


class TradeCrawler:
    def __init__(self, coin_pair: CoinPair, trade_provider: TradeProvider, store: StrategyStore):
        self.coin_pair = coin_pair
        self.trade_provider = trade_provider
        self.store = store

    def crawl(self):
        last_trade_id = self.store.get_last_trade_id()
        trades = self.trade_provider.get_trades(self.coin_pair, last_trade_id)
        self.store.save_trades(trades)

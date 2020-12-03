import logging
from datetime import timedelta
from decimal import Decimal
from typing import List

from trader.spot.account_provider import AccountProvider
from trader.spot.api.spot_api import SpotApi
from trader.spot.data_provider import BookTickerProvider, InstrumentInfoProvider
from trader.spot.order_executor import OrderExecutorProvider, OrderExecutor
from trader.spot.order_executor.limit_gtc_order_executor import LimitGtcOrderExecutor
from trader.spot.trade_provider import TradeProvider
from trader.spot.types import CoinPair, SpotInstrumentInfo, Trade
from trader.spot.types.book_ticker import BookTicker

log = logging.getLogger("spot-trading")


class GridStrategyAdapter(BookTickerProvider, AccountProvider, OrderExecutorProvider, InstrumentInfoProvider,
                          TradeProvider):

    def __init__(self, spot_api: SpotApi, order_query_interval: timedelta, order_cancel_timeout: timedelta):
        """
        构造函数

        Args:
            spot_api (SpotApi): 现货 API 实例
            order_query_interval (timedelta): 订单查询间隔
            order_cancel_timeout (timedelta): 下单至取消订单之间的间隔
        """
        self.spot_api = spot_api
        self.order_query_interval = order_query_interval
        self.order_cancel_timeout = order_cancel_timeout

    def get_book_ticker(self, coin_pair: CoinPair) -> BookTicker:
        """
        获取最优报价

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            最优报价
        """
        return self.spot_api.get_book_ticker(coin_pair)

    def get_balance_by_symbol(self, asset_symbol: str) -> (Decimal, Decimal):
        """
        获取币种数量

        Args:
            asset_symbol (str): 资产币种

        Returns:
            币种数量（可用，冻结）
        """
        return self.spot_api.get_balance_by_symbol(asset_symbol)

    def get_order_executor(self) -> OrderExecutor:
        """
        创建订单执行器

        Returns:
            订单执行器
        """
        return LimitGtcOrderExecutor(self.spot_api,
                                     self.order_query_interval,
                                     self.order_cancel_timeout)  # 订单执行器是无状态的，可以仅创建一次

    def get_instrument_info(self, coin_pair: CoinPair) -> SpotInstrumentInfo:
        """
        获取现货商品信息

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            现货商品信息
        """
        return self.spot_api.get_instrument_info(coin_pair)

    def get_trades(self, coin_pair: CoinPair, trade_id: str = None) -> List[Trade]:
        """
        获取成交记录列表
        Args:
            coin_pair (CoinPair): 币对
            trade_id (str): 交易 id

        Returns:
            交易记录列表
        """
        return self.spot_api.get_trades(coin_pair, trade_id)

    def cancel_all_orders(self, coin_pair: CoinPair):
        self.spot_api.cancel_all(coin_pair)

import logging
from datetime import timedelta
from decimal import Decimal
from functools import wraps
from typing import List

from trader.futures.account_provider import AccountProvider
from trader.futures.api.futures_api import FuturesApi
from trader.futures.data_provider import InstrumentInfoProvider
from trader.futures.order_executor import OrderExecutorProvider, OrderExecutor
from trader.futures.order_executor.stop_gtc_order_executor import StopGtcOrderExecutor
from trader.futures.trade_provider import TradeProvider
from trader.futures.types import ContractPair, FuturesInstrumentInfo, Asset
from trader.spot.types import CoinPair, Trade

logger = logging.getLogger("future-trading")


def retry(retry_times=3):
    def f(func):
        @wraps(func)
        def new_f(*args, **kwargs):
            num_tries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if num_tries < retry_times:
                        logger.exception(f"重试第{num_tries}次,"
                                         f" function: {func.__name__}, "
                                         f"args: {args}, kwargs: {kwargs}")
                        num_tries += 1
                    else:
                        raise e
        return new_f
    return f


class RBreakerStrategyAdapter(AccountProvider, OrderExecutorProvider, InstrumentInfoProvider,
                              TradeProvider):

    def __init__(self, futures_api: FuturesApi, order_query_interval: timedelta, order_cancel_timeout: timedelta):
        """
        构造函数

        Args:
            futures_api (FuturesApi): 合约 API 实例
            order_query_interval (timedelta): 订单查询间隔
            order_cancel_timeout (timedelta): 下单至取消订单之间的间隔
        """
        self.futures_api = futures_api
        self.order_query_interval = order_query_interval
        self.order_cancel_timeout = order_cancel_timeout

    def get_order_executor(self) -> OrderExecutor:
        return StopGtcOrderExecutor(self.futures_api, self.order_query_interval, self.order_cancel_timeout)

    def get_instrument_info(self, contract_pair: ContractPair) -> FuturesInstrumentInfo:
        return self.futures_api.get_instrument_info(contract_pair)

    def cancel_all_orders(self, contract_pair: ContractPair):
        return self.futures_api.cancel_all(contract_pair)

    def get_asset_by_symbol(self, asset_symbol: str) -> Asset:
        return self.futures_api.get_asset_by_symbol(asset_symbol)

    def klines(self, contract_pair: ContractPair, interval: str, **kwargs):
        return self.futures_api.klines(contract_pair, interval, **kwargs)

    def get_position(self, contract_pair: ContractPair):
        return self.futures_api.get_position(contract_pair)

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List

from trader.credentials import Credentials
from trader.spot.types import CoinPair, SpotInstrumentInfo, OrderSide, TimeInForce
from trader.spot.types.book_ticker import BookTicker
from trader.spot.types.order_types import Order, Trade


class SpotApi(ABC):

    def __init__(self, credentials: Credentials = None):
        """
        构造函数

        Args:
            credentials (Credentials): 凭证，如果为 None 不能执行交易相关操作
        """
        self.credentials = credentials

    @abstractmethod
    def get_instrument_info(self, coin_pair: CoinPair) -> SpotInstrumentInfo:
        """
        获取现货交易商品信息

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            现货交易商品信息
        """

    @abstractmethod
    def get_book_ticker(self, coin_pair: CoinPair) -> BookTicker:
        """
        获取最优报价

        Args:
            coin_pair (CoinPair): 币对

        Returns:
            最优报价
        """

    @abstractmethod
    def get_balance_by_symbol(self, asset_symbol: str) -> (Decimal, Decimal):
        """
        获取资产余额

        Args:
            asset_symbol (str): 资产币种

        Returns:
            可用数量, 冻结数量
        """

    @abstractmethod
    def create_limit_order(self, coin_pair: CoinPair, order_side: OrderSide, price: Decimal, qty: Decimal,
                           tif: TimeInForce) -> Order:
        """
        创建限价单

        Args:
            coin_pair (CoinPair): 币对
            order_side (OrderSide): 买卖方向
            price (Decimal): 价格
            qty (Decimal): 数量
            tif (TimeInForce): 有效时间类型

        Returns:
            订单
        """

    @abstractmethod
    def cancel_order(self, coin_pair: CoinPair, order_id: str) -> Order:
        """
        取消订单

        Args:
            coin_pair (CoinPair): 币对
            order_id (str): 订单id

        Returns:
            订单
        """

    @abstractmethod
    def query_order(self, coin_pair: CoinPair, order_id: str) -> Order:
        """
        查询订单

        Args:
            coin_pair (CoinPair): 币对
            order_id (str): 订单id

        Returns:
            订单
        """

    @abstractmethod
    def cancel_all(self, coin_pair: CoinPair) -> List[Order]:
        """
        取消所有未成交订单

        Args:
            coin_pair (CoinPair): 币对

        Returns:

        """

    @abstractmethod
    def get_trades(self, coin_pair: CoinPair, from_trade_id: str = None) -> List[Trade]:
        """
        获取指定 trade_id 之后的交易记录列表

        Args:
            coin_pair (CoinPair): 币对
            from_trade_id (str): 交易记录id

        Returns:
            交易记录列表
        """

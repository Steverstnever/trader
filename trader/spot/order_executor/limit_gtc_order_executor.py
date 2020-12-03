import time
from datetime import timedelta, datetime
from decimal import Decimal

from trader.spot.api.spot_api import SpotApi
from trader.spot.order_executor import OrderExecutor
from trader.spot.types import OrderSide, CoinPair
from trader.spot.types.order_types import Order, TimeInForce


class StopWatch:
    def __init__(self, timeout: timedelta):
        self.started_at = datetime.now()
        self.timeout = timeout

    def reset(self):
        self.started_at = datetime.now()

    def is_timeout(self):
        return datetime.now() - self.started_at > self.timeout


class LimitGtcOrderExecutor(OrderExecutor):
    def __init__(self, spot_api: SpotApi, order_query_interval: timedelta, order_cancel_timeout: timedelta):
        self.spot_api = spot_api
        self.order_query_interval = order_query_interval
        self.order_cancel_timeout = order_cancel_timeout

    def _place_order(self, coin_pair: CoinPair, order_side: OrderSide, price: Decimal, qty: Decimal) -> Order:

        # 下订单
        order: Order = self.spot_api.create_limit_order(coin_pair=coin_pair,
                                                        order_side=order_side,
                                                        price=price,
                                                        qty=qty,
                                                        tif=TimeInForce.GTC)
        if order.status.is_completed():
            return order

        # 设置取消超时时间
        stopwatch = StopWatch(self.order_cancel_timeout)
        while not stopwatch.is_timeout():
            # 查询订单
            time.sleep(self.order_query_interval.total_seconds())
            order: Order = self.spot_api.query_order(coin_pair=coin_pair, order_id=order.order_id)
            if order.status.is_completed():
                return order

        # 超时后取消订单
        order: Order = self.spot_api.cancel_order(coin_pair=coin_pair, order_id=order.order_id)
        return order

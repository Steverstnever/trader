import time
from datetime import timedelta, datetime
from decimal import Decimal

from trader.futures.api.futures_api import FuturesApi
from trader.futures.order_executor import OrderExecutor
from trader.futures.types import OrderSide, ContractPair, PositionSide
from trader.futures.types.order_types import Order, TimeInForce


class StopWatch:
    def __init__(self, timeout: timedelta):
        self.started_at = datetime.now()
        self.timeout = timeout

    def reset(self):
        self.started_at = datetime.now()

    def is_timeout(self):
        return datetime.now() - self.started_at > self.timeout


class OrderNotCancelledError(RuntimeError):
    """
    订单没有正确取消的错误

    发生在已经下单，但是没有成功取消订单的情况（比如：在币安平台，取消订单时查询订单id不存在）
    """

    def __init__(self, order: Order, origin_exception: Exception):
        """

        """
        self.order = order
        self.origin_exception = origin_exception


class StopGtcOrderExecutor(OrderExecutor):
    def __init__(self, futures_api: FuturesApi, order_query_interval: timedelta, order_cancel_timeout: timedelta):
        self.futures_api = futures_api
        self.order_query_interval = order_query_interval
        self.order_cancel_timeout = order_cancel_timeout

    def _place_order(self, contract_pair: ContractPair,
                     order_side: OrderSide, position_side: PositionSide, price: Decimal,
                     stop_price: Decimal, qty: Decimal, **kwargs) -> Order:
        # 下订单
        client_order_id = self.futures_api.gen_client_order_id()
        order: Order = self.futures_api.create_stop_order(client_order_id=client_order_id,
                                                          contract_pair=contract_pair,
                                                          order_side=order_side,
                                                          position_side=position_side,
                                                          price=price,
                                                          stop_price=stop_price,
                                                          qty=qty,
                                                          tif=TimeInForce.GTC,
                                                          **kwargs)
        if order.status.is_completed():
            return order
        try:
            # 设置取消超时时间
            stopwatch = StopWatch(self.order_cancel_timeout)
            while not stopwatch.is_timeout():
                # 查询订单
                time.sleep(self.order_query_interval.total_seconds())
                order: Order = self.futures_api.query_order(contract_pair=contract_pair,
                                                            client_order_id=client_order_id,
                                                            order_id=order.order_id)
                if order.status.is_completed():
                    return order

            # 超时后取消订单
            order: Order = self.futures_api.cancel_order(contract_pair=contract_pair,
                                                         client_order_id=client_order_id,
                                                         order_id=order.order_id)
            return order
        except Exception as e:
            raise OrderNotCancelledError(order, e)

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .coin_pair import CoinPair


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


class TimeInForce(Enum):
    GTC = "Good-Till-Cancel"
    FOK = "Fill-Or-Kill"
    IOC = "Immediate-Or-Cancel"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

    # TODO: 处理下述高级订单类型
    # STOP_LOSS = 'STOP_LOSS'
    # STOP_LOSS_LIMIT = 'STOP_LOSS_LIMIT'
    # TAKE_PROFIT = 'TAKE_PROFIT'
    # TAKE_PROFIT_LIMIT = 'TAKE_PROFIT_LIMIT'
    # LIMIT_MAKER = 'LIMIT_MAKER'


class OrderStatus(Enum):
    NEW = 'NEW'
    PARTIALLY_FILLED = 'PARTIALLY_FILLED'
    FILLED = 'FILLED'
    CANCELED = 'CANCELED'
    PENDING_CANCEL = 'PENDING_CANCEL'
    REJECTED = 'REJECTED'
    EXPIRED = 'EXPIRED'

    def is_completed(self):
        return self in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.EXPIRED)


@dataclass()
class Order:
    """
    订单
    """
    coin_pair: CoinPair

    order_id: str
    client_order_id: str

    tif: TimeInForce

    price: Decimal
    qty: Decimal

    filled_qty: Decimal

    order_side: OrderSide
    status: OrderStatus
    type: OrderType

    time: datetime

    # binance 返回格式:
    # {'clientOrderId': '9bHVLj9iNoVQkzq7oRByrl',
    #  'cummulativeQuoteQty': '0.00000000',
    #  'executedQty': '0.00000000',
    #  'fills': [],
    #  'orderId': 1057791006,
    #  'orderListId': -1,
    #  'origQty': '1.00100000',
    #  'price': '10.12340000',
    #  'side': 'BUY',
    #  'status': 'NEW',
    #  'symbol': 'BNBUSDT',
    #  'timeInForce': 'GTC',
    #  'transactTime': 1606665799609,
    #  'type': 'LIMIT'}


@dataclass
class OrderResult:
    order_id: str  # 订单id
    coin_pair: CoinPair  # 币对
    price: Decimal  # 订单价格
    qty: Decimal  # 订单数量
    side: OrderSide  # 订单方向（买、卖）
    timestamp: datetime  # 时间戳

    avg_price: Decimal  # 平均价格
    filled: Decimal  # 实际成交数据
    commission: Decimal  # 佣金


@dataclass
class Trade:
    coin_pair: CoinPair  # 币对
    trade_id: str  # 成交记录id
    order_id: str  # 订单id
    price: Decimal  # 价格
    qty: Decimal  # 成交数量
    commission: Decimal  # 手续费
    commission_asset: str  # 手续费币种
    timestamp: datetime  # 创建时间记录的本地时间（注意：不是服务器时间）
    order_side: OrderSide  # 买卖方向
    is_marker: bool  # 是否是 maker
    is_best_match: bool  # 是否是最佳匹配

    @property
    def compact_display_str(self):
        return f"{self.coin_pair.symbol}, trade_id={self.trade_id}, order_id={self.order_id}, " \
               f"price={str(self.price)}, qty={self.qty}, " \
               f"commission={str(self.commission)} [{self.commission_asset}]， time={self.timestamp.isoformat()}, " \
               f"side={self.order_side.name}, is_maker: {self.is_marker}, is_best_match: {self.is_best_match}"

    def __str__(self):
        return self.compact_display_str
    # 币安返回格式：
    # {
    #     "id": 28457,
    #     "price": "4.00000100",
    #     "qty": "12.00000000",
    #     "commission": "10.10000000",
    #     "commissionAsset": "BNB",
    #     "time": 1499865549590,
    #     "isBuyer": true,
    #     "isMaker": false,
    #     "isBestMatch": true
    # }

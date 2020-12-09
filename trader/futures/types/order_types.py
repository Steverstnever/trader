from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .symbol import ContractPair


class OrderSide(Enum):
    BUY = 'buy'
    SELL = 'sell'


class PositionSide(Enum):
    LONG = 'long'
    SHORT = 'short'
    BOTH = 'both'


class TimeInForce(Enum):
    GTC = "Good-Till-Cancel"
    FOK = "Fill-Or-Kill"
    IOC = "Immediate-Or-Cancel"


class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = 'STOP'
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
    client_order_id: str
    contract_pair: ContractPair
    executed_qty: Decimal   # 成交量(张数)
    order_id: str  # 系统订单号
    avg_price: Decimal  # 平均成交价
    order_side: OrderSide
    position_side: PositionSide  # 持仓方向
    status: OrderStatus
    type: OrderType


@dataclass
class OrderResult:
    order_id: str  # 订单id
    contract_pair: ContractPair  # 币对
    price: Decimal  # 订单价格
    qty: Decimal  # 订单数量
    side: OrderSide  # 订单方向（买、卖）
    timestamp: datetime  # 时间戳

    avg_price: Decimal  # 平均价格
    filled: Decimal  # 实际成交数据
    commission: Decimal  # 佣金


@dataclass
class Trade:
    contract_pair: ContractPair  # 币对
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
        return f"{self.contract_pair.symbol}, trade_id={self.trade_id}, order_id={self.order_id}, " \
               f"price={str(self.price)}, qty={self.qty}, " \
               f"commission={str(self.commission)} [{self.commission_asset}]， time={self.timestamp.isoformat()}, " \
               f"side={self.order_side.name}, is_maker: {self.is_marker}, is_best_match: {self.is_best_match}"

    def __str__(self):
        return self.compact_display_str

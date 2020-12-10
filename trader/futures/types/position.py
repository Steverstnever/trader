from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from .symbol import ContractPair


@dataclass
class Position:
    symbol: ContractPair
    position_amt: Decimal
    entry_price: Decimal  # 开仓均价
    mark_price: Decimal  # 当前标记价格
    position_side: "PositionSide"


class PositionSide(Enum):
    LONG = 'long'
    SHORT = 'short'
    BOTH = 'both'
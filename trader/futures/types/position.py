from dataclasses import dataclass
from decimal import Decimal

from trader.futures.types import ContractPair, PositionSide


@dataclass
class Position:
    symbol: ContractPair
    position_amt: Decimal
    entry_price: Decimal  # 开仓均价
    mark_price: Decimal  # 当前标记价格
    position_side: PositionSide

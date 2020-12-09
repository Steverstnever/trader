from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Asset:
    asset: str  # 资产名
    walletBalance: Decimal  # 账户余额
    marginBalance: Decimal  # 保证金余额
    availableBalance: Decimal  # 可用下单余额

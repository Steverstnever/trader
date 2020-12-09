from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Asset:
    asset_symbol: str  # 资产名
    wallet_balance: Decimal  # 账户余额
    margin_balance: Decimal  # 保证金余额
    available_balance: Decimal  # 可用下单余额

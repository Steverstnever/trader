from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class AccountSnapshot:
    asset: str  # 资产或者现金
    asset_qty: Decimal  # 资产余额（可用+余额）
    cash: str  # 现金币种
    cash_qty: Decimal  # 现金余额（可用+余额）
    price: Decimal  # 汇率
    timestamp: datetime  # 时间戳

    @property
    def total_cash_qty(self):
        return self.asset_qty * self.price + self.cash_qty

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, MAX_EMAX
from enum import Enum

from trader.spot.types import CoinPair


class FuturesContact:
    SEPARATOR = '@'
    DELIVERY_DATE_FORMAT = '%y%m%d'

    def __init__(self, underlying_asset: CoinPair, delivery_date: date):
        self.underlying_asset = underlying_asset
        self.delivery_date = delivery_date

    @property
    def symbol(self) -> str:
        """
        生成通用格式交割合约id

        Returns:
            通用格式交割合约id
        """
        return f"{self.underlying_asset.symbol}{self.SEPARATOR}{self.delivery_date.strftime(self.DELIVERY_DATE_FORMAT)}"

    @classmethod
    def from_symbol(cls, symbol: str) -> "FuturesContact":
        coin_pair_symbol, date_str = symbol.split(cls.SEPARATOR, 2)
        underlying_asset = CoinPair.from_symbol(coin_pair_symbol)
        delivery_date = datetime.strptime(date_str, cls.DELIVERY_DATE_FORMAT).date()
        return cls(underlying_asset, delivery_date)

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return self.symbol


class FuturesContractAlias(Enum):
    NEXT_QUARTER = "next quarter"
    THIS_QUARTER = "this quarter"
    NEXT_WEEK = "next week"
    THIS_WEEK = "this week"
    NOT_WITHIN_DATE_RANGE = "not in validated date range"


@dataclass
class FuturesInstrumentInfo:
    contract: FuturesContact

    contract_value: Decimal  # 合约面值
    contract_value_currency_symbol: str  # 合约面值计价币种

    listing_time: datetime  # 上线时间（on-board-time）

    min_price_size: Decimal  # 价格精度
    min_qty_size: Decimal  # 数量精度

    is_inverse: bool  # 币本位还是 U本位

    max_price: Decimal = Decimal(MAX_EMAX)  # 最大价格
    min_price: Decimal = Decimal(0)  # 最小价格

    max_qty: Decimal = Decimal(MAX_EMAX)  # 最大数量
    min_qty: Decimal = Decimal(0)  # 最小数量

    min_notional: Decimal = Decimal(0)  # 最小名义价格（下单时的：price*qty）

    def asset_symbol(self):
        return self.contract.underlying_asset.asset_symbol

    def cash_symbol(self):
        return self.contract.underlying_asset.cash_symbol

    @property
    def alias(self) -> FuturesContractAlias:
        # TODO: 合约别名
        # timediff = self.contract.delivery_date - date.today()
        return FuturesContractAlias.NOT_WITHIN_DATE_RANGE


@dataclass
class BookTicker:
    contract: FuturesContact  # 合约
    time: datetime  # 时间戳
    bid1_price: Decimal  # 最优买单价
    bid1_qty: Decimal  # 最优买单挂单量
    ask1_price: Decimal  # 最优卖单价
    ask1_qty: Decimal  # 最优卖单挂单量

import json

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Bar:
    open_time: datetime
    open_price: Decimal
    close_price: Decimal
    high: Decimal
    low: Decimal
    volume: Decimal

    def to_dict(self):
        return {
            'open_time': self.open_time,
            'open_price': self.open_price,
            'close_price': self.close_price,
            'high': self.high,
            'low': self.low,
            'volume': self.volume
        }

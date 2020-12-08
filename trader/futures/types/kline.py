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


class Kline:
    def __init__(self, size):
        self.size = size
        self.data = []
        self.full = False

    def append(self, bar: Bar):
        if not self.data:
            self.data.append(bar)
        elif self.data[-1].open_time == bar.open_time:
            self.data[-1] = bar
        elif self.data[-1].open_time < bar.open_time:
            last_bar = self.data[-1]
            self.data.append(bar)
            if len(self.data) > self.size:
                self.data = self.data[1:]
                return last_bar

    def to_json(self):
        result = []
        for each in self.data:
            result.append(each.to_dict())
        return json.dumps(result)

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

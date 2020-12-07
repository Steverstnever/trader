from decimal import Decimal

from trader.strategy.grid.grid_position_manager import GridPositionManager
from trader.strategy.grid.grid_utils import create_geometric_sequence

# class SpotInstrument:
#     def __init__(self, symbol):
#         self.min_price_size = Decimal()
#         self.min_qty_size = Decimal()
#         self.symbol = symbol
#         self.levels = []
#
#     def get_current_cash(self):
#         """从交易所 API 中获取当前账户现金"""
#         # TODO:
#         return Decimal(10000)
#
#     def init_grid(self, low: Decimal, high: Decimal, sample_seq: list, total_position: Decimal):
#         prices = grid_tools.grid_prices(low, high, sample_seq)
#         total_price_gap = high - low
#         self.levels.clear()
#         for p in zip(prices, prices[1:]):
#             level_position = ((p[1] - p[0]) / total_price_gap) * total_position
#             level = Level(low_price=p[0], high_price=p[1], max_position=level_position)
#             self.levels.append(level)
#         pprint(self.levels)
#         print(sum(l.max_position for l in self.levels))
#         # print(json.dumps(self.__dict__, indent=4))
#
#
# instrument = SpotInstrument("BTC-USDT")
# instrument.init_grid(Decimal(3), Decimal(6), create_geometric_sequence(10, 1.2), Decimal(10000))



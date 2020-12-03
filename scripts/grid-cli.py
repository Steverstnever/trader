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


# TODO: 移植到单元测试中
grid = GridPositionManager(Decimal(2), Decimal(6), create_geometric_sequence(5, 1), Decimal(10000))

p = grid.fill_positions(Decimal(2500), Decimal(4))
print(f"填充网格后还剩: {str(p)}")

grid.log_levels()

market_price = Decimal(3)
p = grid.get_positions_to_buy(market_price)
print(f"市价 {market_price}, 还可以买: {str(p)}")

grid.bought_position(Decimal(1500))
print(f"买入 {Decimal(1500)}资产")
grid.log_levels()

market_price = Decimal(5.5)
p = grid.get_positions_to_sell(market_price)
print(f"市价 {market_price}, 还可以卖: {str(p)}")

p = grid.sold_position(Decimal(5000))
print(f"卖出 {Decimal(5000)} 资产，空仓后还有 {p}")
grid.log_levels()

grid.clear_positions()
grid.log_levels()

for pos in range(100, 1000, 100):
    grid.bought_position(Decimal(pos))
    print(f" <<< BOUGHT {pos} >>> ".center(80))
    grid.log_levels()

for pos in range(100, 5000, 80):
    grid.sold_position(Decimal(pos))
    print(f" <<< SOLD {pos} >>> ".center(80))
    grid.log_levels()

grid.clear_positions()
p = grid.get_positions_to_buy(Decimal(0))
print(f"{p}")
grid.bought_position(p)
p = grid.get_positions_to_sell(Decimal(10))
print(f"{p}")
grid.log_levels()

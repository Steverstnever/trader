# 生成网格
from decimal import Decimal
from pathlib import Path

from trader.strategy.grid.grid_generators import GeometricGridGenerator, ArithmeticGridGenerator, \
    MixedGridGenerator, ConfigGridGenerator
from trader.strategy.grid.grid_position_manager import GridPositionManager

g = ArithmeticGridGenerator(Decimal("10000"), Decimal("20000"), 20, Decimal("0.1"))
for i, level in enumerate(g.generate()):
    print(f"{i} => {level}")

gpp = GridPositionManager(g)
gpp.log_levels()

print('-' * 80)
print()

# g = GeometricGridGenerator(Decimal("10000"), Decimal("20000"), 20, Decimal("0.1"))
# print(g.description().center(80, '*'))
# for i, level in enumerate(g.generate()):
#     print(f"{i} => {level}")
#
g = GeometricGridGenerator(Decimal("10000"), Decimal("20000"), 20, Decimal("0.1"))
print(g.description().center(80, '*'))
for i, level in enumerate(g.generate()):
    print(f"{i} => {level}")
gpp = GridPositionManager(g, level_min_profit=Decimal("0.009"))
gpp.log_levels()

g1 = ArithmeticGridGenerator(Decimal("15000"), Decimal("20000"), 10, Decimal("0.2"))
g2 = GeometricGridGenerator(Decimal("10000"), Decimal("15000"), 10, Decimal("0.1"))
g = MixedGridGenerator(g1, g2)
print(g.description().center(80, '*'))
for i, level in enumerate(g.generate()):
    print(f"{i} => {level}")
gpp = GridPositionManager(g, level_min_profit=Decimal("0.009"))
gpp.log_levels()

grid_config_path = Path.cwd() / ".custom_grid.json"
g.export_json(grid_config_path)

g = ConfigGridGenerator(grid_config_path)
print(g.description().center(80, '*'))
for i, level in enumerate(g.generate()):
    print(f"{i} => {level}")
gpp = GridPositionManager(g, level_min_profit=Decimal("0.009"))
gpp.log_levels()

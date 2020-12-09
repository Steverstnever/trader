import math
import time
import random
from decimal import Decimal

import pytest

from trader.strategy.grid.grid_generators import ArithmeticGridGenerator, GeometricGridGenerator, MixedGridGenerator, \
    assert_grid_levels, KBar, VolumeGridGenerator
from trader.strategy.grid.grid_utils import create_volume_profile
from trader.strategy.grid.grid_position_manager import Level, LevelPositionError, GridPositionManager
from trader.utils import is_constant


def test_position_level():
    level = Level(low_price=Decimal('1000'), high_price=Decimal('1100'), max_position=Decimal('5'))

    # 初始值判断
    assert level.price_gap == Decimal('100')
    assert level.is_empty() and not level.is_full()
    assert level.profit_pct == 0.1
    assert level.remaining_position == Decimal('5')
    assert level.remaining_cash_qty == Decimal('5000')
    assert level.cash_qty == Decimal('0')

    assert level.has_remaining_position() and level.remaining_position == Decimal('5')
    assert level.lower_than(Decimal('1101')) and level.higher_than(Decimal('999'))

    # 临界点判断
    assert not level.lower_than(Decimal('1100')) and not level.higher_than(Decimal('1000'))

    # 初始值判断
    assert level.position == Decimal()
    assert level.hold_pct == 0.0

    # 测试增加，减少仓位
    level.inc_position(Decimal('1'))
    assert level.position == Decimal('1')
    assert math.isclose(level.hold_pct, 0.2)
    level.dec_position(Decimal('0.5'))
    assert level.position == Decimal('0.5')
    assert math.isclose(level.hold_pct, 0.1)

    # 判断异常
    with pytest.raises(LevelPositionError):  # 超过剩余
        level.dec_position(Decimal('1'))

    assert level.position == Decimal('0.5')

    with pytest.raises(LevelPositionError):  # 超过最大仓位
        level.dec_position(Decimal('5'))


def test_grid_generator():
    # 等差网格
    grid_gen = ArithmeticGridGenerator(Decimal(1000), Decimal(1100), 20, Decimal('5'))
    levels = grid_gen.generate()
    assert len(levels) == grid_gen.number_of_levels == 20
    assert all([level.price_gap == Decimal('5') for level in levels])
    assert_grid_levels(levels)

    # 等比网格
    grid_gen = GeometricGridGenerator(Decimal(1000), Decimal(1100), 5, Decimal('5'))
    levels = grid_gen.generate()
    assert len(levels) == grid_gen.number_of_levels == 5
    assert is_constant([level.profit_pct for level in levels])  # 等比数列的特征是公比相等
    assert_grid_levels(levels)

    # 混合网格
    gg2 = GeometricGridGenerator(Decimal(1100), Decimal(1200), 10, Decimal('5'))
    gg1 = ArithmeticGridGenerator(Decimal(1000), Decimal(1100), 10, Decimal('5'))
    gg = MixedGridGenerator(gg2, gg1)
    levels = gg.generate()
    assert len(levels) == 20
    assert_grid_levels(levels)


def test_grid_manager():
    """"""
    # 等差网格
    grid_gen = ArithmeticGridGenerator(Decimal('1'), Decimal('3'), 2, Decimal('5'))

    grid = GridPositionManager(grid_gen, level_min_profit=0.05)

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=0, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=0, max_position=5.00000000]

    assert grid.total_max_position == Decimal('10')
    assert grid.total_remaining_position == Decimal('10')
    assert grid.total_position == Decimal()
    assert grid.total_used_cash_qty == Decimal()
    assert grid.total_remaining_cash_qty == Decimal('15')
    assert grid.total_max_cash_qty == Decimal('15')
    assert grid.resistance_price == Decimal('3')
    assert grid.support_price == Decimal('1')

    assert grid.get_positions_to_buy(current_price=Decimal('0.5')) == Decimal('10')
    assert grid.get_positions_to_buy(current_price=Decimal('1.5')) == Decimal('5')
    assert grid.get_positions_to_buy(current_price=Decimal('2.5')) == Decimal('0')
    assert grid.get_positions_to_buy(current_price=Decimal('3.5')) == Decimal('0')

    assert grid.get_positions_to_sell(current_price=Decimal('0.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('1.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('2.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('3.5')) == Decimal('0')

    grid.bought_position(Decimal("2.5"))

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=2.5, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=0, max_position=5.00000000]

    assert grid.total_position == Decimal("2.5")
    assert grid.total_remaining_position == Decimal("7.5")
    assert grid.total_used_cash_qty == Decimal("5")
    assert grid.total_remaining_cash_qty == Decimal("10")

    assert grid.get_positions_to_sell(current_price=Decimal('0.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('1.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('2.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('3.5')) == Decimal('2.5')

    grid.bought_position(Decimal("5"))

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=5, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=2.5, max_position=5.00000000]

    assert grid.total_position == Decimal("7.5")
    assert grid.total_remaining_position == Decimal("2.5")
    assert grid.total_used_cash_qty == Decimal("12.5")
    assert grid.total_remaining_cash_qty == Decimal("2.5")

    assert grid.get_positions_to_buy(current_price=Decimal('0.5')) == Decimal('2.5')
    assert grid.get_positions_to_buy(current_price=Decimal('1.5')) == Decimal('0')
    assert grid.get_positions_to_buy(current_price=Decimal('2.5')) == Decimal('0')
    assert grid.get_positions_to_buy(current_price=Decimal('3.5')) == Decimal('0')

    assert grid.get_positions_to_sell(current_price=Decimal('0.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('1.5')) == Decimal('0')
    assert grid.get_positions_to_sell(current_price=Decimal('2.5')) == Decimal('2.5')
    assert grid.get_positions_to_sell(current_price=Decimal('3.5')) == Decimal('7.5')

    grid.sold_position(Decimal("3"))

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=4.5, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=0, max_position=5.00000000]

    assert grid.total_position == Decimal("4.5")
    assert grid.total_remaining_position == Decimal("5.5")
    assert grid.total_used_cash_qty == Decimal("9")
    assert grid.total_remaining_cash_qty == Decimal("6")

    overflow_pos = grid.sold_position(Decimal("5"))
    assert overflow_pos == Decimal("0.5")

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=0, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=0, max_position=5.00000000]

    assert grid.total_position == Decimal("0")
    assert grid.total_remaining_position == Decimal("10")
    assert grid.total_used_cash_qty == Decimal("0")
    assert grid.total_remaining_cash_qty == Decimal("15")

    grid.bought_position(Decimal("7.5"))

    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=5, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=2.5, max_position=5.00000000]

    grid.clear_positions()
    # 当前网格：
    # 0 => [2.00000000->3.00000000, position=0, max_position=5.00000000]
    # 1 => [1.00000000->2.00000000, position=0, max_position=5.00000000]

    assert grid.total_max_position == Decimal('10')
    assert grid.total_remaining_position == Decimal('10')
    assert grid.total_position == Decimal()
    assert grid.total_used_cash_qty == Decimal()
    assert grid.total_remaining_cash_qty == Decimal('15')
    assert grid.total_max_cash_qty == Decimal('15')
    assert grid.resistance_price == Decimal('3')
    assert grid.support_price == Decimal('1')

    assert grid.get_positions_to_buy(current_price=Decimal('0.5')) == Decimal('10')
    assert grid.get_positions_to_buy(current_price=Decimal('1.5')) == Decimal('5')
    assert grid.get_positions_to_buy(current_price=Decimal('2.5')) == Decimal('0')
    assert grid.get_positions_to_buy(current_price=Decimal('3.5')) == Decimal('0')


def test_volume_profile_grid():
    k_line = list()
    for i in range(300):
        low = random.uniform(i + 10, i + 20)
        high = random.uniform(i + 20, i + 30)
        open_ = random.uniform(low, high)
        close = random.uniform(low, high)
        vol = random.uniform(1, 300)
        k_line.append(KBar(id_=str(time.time()), open=Decimal(open_),
                           close=Decimal(close), high=Decimal(high),
                           low=Decimal(low),
                           vol=Decimal(vol)))
    g = VolumeGridGenerator(Decimal("50.0001"), Decimal("257.02"), 10,
                            Decimal("200"), create_volume_profile(k_line))
    for level in g.generate():
        print(level)

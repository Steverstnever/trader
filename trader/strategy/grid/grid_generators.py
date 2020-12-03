import json
import math
from abc import ABC
from decimal import Decimal
from pathlib import Path
from typing import List

from trader.strategy.grid.grid_position_manager import GridGenerator, Level


class AlgorithmGridGenerator(GridGenerator, ABC):

    def __init__(self, support_price: Decimal, resistance_price: Decimal, number_of_levels: int,
                 max_position_per_level: Decimal):
        """
                构造函数

                Args:
                    support_price (Decimal): （价格）支撑位
                    resistance_price (Decimal): (价格) 阻力位
                    number_of_levels (int): 等级数
                    max_position_per_level (Decimal): 每级别最大仓位
                """
        assert resistance_price > support_price, "阻力位价格必须大于支撑位价格"
        assert number_of_levels > 1, "网格数必须 > 1"

        self.support_price = support_price
        self.resistance_price = resistance_price
        self.number_of_levels = number_of_levels
        self.max_position_per_level = max_position_per_level

    @property
    def price_gap(self):
        """
        价差
        """
        return self.resistance_price - self.support_price


class ArithmeticGridGenerator(AlgorithmGridGenerator):
    """
    等差网格生成器
    """

    def __init__(self, support_price: Decimal, resistance_price: Decimal, number_of_levels: int,
                 max_position_per_level: Decimal):
        super().__init__(support_price, resistance_price, number_of_levels, max_position_per_level)

    def generate(self) -> List[Level]:
        level_price_gap = self.price_gap / self.number_of_levels

        result: List[Level] = []
        high_price = self.resistance_price
        while high_price > self.support_price:
            low_price = high_price - level_price_gap
            result.append(Level(low_price, high_price, self.max_position_per_level))
            high_price = low_price
        return result

    def description(self) -> str:
        return f"等差网格 [支撑位 {self.support_price}, 阻力位 {self.resistance_price}, " \
               f"网格数 {self.number_of_levels}, 每格最大仓位: {self.max_position_per_level}] "


class GeometricGridGenerator(AlgorithmGridGenerator):
    """
    等比网格生成器
    """

    def __init__(self, support_price: Decimal, resistance_price: Decimal, number_of_levels: int,
                 max_position_per_level: Decimal):
        super().__init__(support_price, resistance_price, number_of_levels, max_position_per_level)

    @property
    def common_factor(self):
        return 1 if self.number_of_levels == 1 \
            else math.pow(self.resistance_price / self.support_price, 1 / (self.number_of_levels - 1))

    def generate(self) -> List[Level]:
        """从高到低等比网格，价格高时，每格价差大"""
        result: List[Level] = []
        high_price = self.resistance_price
        while high_price > self.support_price:
            low_price = high_price / Decimal.from_float(self.common_factor)
            result.append(Level(low_price, high_price, self.max_position_per_level))
            high_price = low_price
        return result

    def description(self) -> str:
        return f"等比网格 [支撑位 {self.support_price}, 阻力位 {self.resistance_price}, " \
               f"网格数 {self.number_of_levels}, 每格最大仓位: {self.max_position_per_level}] "


class MixedGridGenerator(GridGenerator):
    def __init__(self, *generators):
        self.generators = generators

    def generate(self) -> List[Level]:
        result: List[Level] = []
        last_support_price = self.generators[0].resistance_price
        for g in self.generators:
            if last_support_price != g.resistance_price:
                raise RuntimeError(f"混合网格生成器中的各个子生成器必须连续，从高到低，此生成器价格设置有错误： {g.description()}")
            levels = g.generate()
            result.extend(levels)
            last_support_price = g.support_price
        return result

    def description(self) -> str:
        return f"混合网格: [{'; '.join(g.description() for g in self.generators)}]"


class ConfigGridGenerator(GridGenerator):

    def __init__(self, config_path: Path):
        self.config_path = config_path

    def generate(self) -> List[Level]:
        levels = json.loads(self.config_path.read_bytes())
        result: List[Level] = []
        for row in levels:
            low_price, high_price, max_pos = row
            result.append(
                Level(low_price=Decimal(low_price), high_price=Decimal(high_price), max_position=Decimal(max_pos)))
        return result

    def description(self) -> str:
        return f"自定义配置网格：从 {self.config_path} 装载网格配置"

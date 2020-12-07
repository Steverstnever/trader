import json
import logging
from abc import abstractmethod, ABC
from decimal import Decimal, MAX_EMAX
from pathlib import Path
from typing import List

log = logging.getLogger("grid-position-manager")


class LevelPositionError(RuntimeError):
    """
    仓位错误
    """


class Level:
    """代表一个格子

    注意：格子的仓位指资产数量
    """

    def __init__(self, low_price: Decimal, high_price: Decimal, max_position: Decimal):
        """
        构造函数

        Args:
            low_price (Decimal): 格子最低价（下限）
            high_price (Decimal): 格子最高价（上限）
            max_position (Decimal): （满仓）最大仓位（资产数量）
        """

        assert high_price > low_price, "网格中高价必须大于低价"
        assert max_position > Decimal(0), "网格最大仓位必须大于0"
        self.low_price = low_price
        self.high_price = high_price
        self.max_position = max_position
        self.position = Decimal(0)  # 当前持仓（资产数量）

    def lower_than(self, price: Decimal) -> bool:
        """
        判断格子在指定价格下方（格子上限低于价格）

        Args:
            price (Decimal): 指定价格

        Returns:
            true 格子低于价格（格子上限低于指定价格）
        """
        return self.high_price < price

    def higher_than(self, price: Decimal) -> bool:
        """
        判断格子在指定价格上方（格子下限高于价格）

        Args:
            price (Decimal): 指定价格

        Returns:
            true 在格子上方（格子下限高于指定价格）
        """
        return self.low_price > price

    @property
    def remaining_position(self) -> Decimal:
        """
        剩余仓位（未填充仓位）

        Returns:
            格子还可以容纳的仓位
        """
        return self.max_position - self.position

    def has_remaining_position(self) -> bool:
        """
        是否有剩余仓位

        Returns:
            true 还有剩余仓位
        """
        return self.remaining_position > Decimal(0)

    def inc_position(self, position: Decimal):
        """
        增持仓位

        Args:
            position (Decimal): 仓位数量
        Raises:
            RuntimeError: 增持仓位超过剩余仓位
        """
        if position > self.remaining_position:
            raise LevelPositionError("增持仓位超过剩余仓位")
        self.position += position

    def dec_position(self, position: Decimal):
        """
        减持仓位

        Args:
            position (Decimal):  仓位数量
        Raises:
            RuntimeError: 减持仓位超过当前持仓
        """
        if position > self.position:
            raise LevelPositionError("减持仓位超过当前持仓")
        self.position -= position

    def is_empty(self) -> bool:
        """
        判断是否空仓

        Returns:
            true 空仓
        """
        return self.position == Decimal(0)

    def is_full(self) -> bool:
        """
        判断是否满仓

        Returns:
            true 满仓
        """
        return self.position == self.max_position

    @property
    def hold_pct(self) -> float:
        """
        持仓百分比

        Returns:
            持仓百分比
        """
        return self.position / self.max_position

    @property
    def price_gap(self) -> Decimal:
        """
        价差

        Returns:
            价差
        """
        return self.high_price - self.low_price

    # @property
    # def profit(self) -> Decimal:
    #     """
    #     盈利数量（按照资产计价）
    #
    #     Returns:
    #         盈利数量
    #     """
    #     return self.max_position
    #
    @property
    def profit_cash(self) -> Decimal:
        """
        按照现金计价的最大盈利

        Returns:
            按照现金计价的最大盈利 (max_position * high_price - max_position * low_price)
        """
        return self.price_gap * self.max_position

    @property
    def profit_pct(self) -> float:
        """
        网格收益率（未排除手续费）

        Returns:
            网格收益率
        """
        return float(self.price_gap / self.low_price)

    @property
    def max_cash_qty(self) -> Decimal:
        """
        最大仓位对应的现金数量

        Returns:
            现金数量
        """
        return self.max_position * self.low_price

    @property
    def cash_qty(self) -> Decimal:
        """
        当前持有仓位对应的现金数量

        Returns:
            现金数量
        """
        return self.position * self.low_price

    @property
    def remaining_cash_qty(self) -> Decimal:
        """
        填满此格子需要的现金数量

        Returns:
            填满此格子需要的现金数量
        """
        return self.remaining_position * self.low_price

    @property
    def compact_display_str(self):
        price_info = f"[{self.low_price:0.8f}->{self.high_price:0.8f}, {self.price_gap:0.8f}]"
        pos_info = f"({self.position:0.8f}/${self.cash_qty:0.8f} of {self.max_position:0.8f}/${self.max_cash_qty:0.8f} = {self.hold_pct * 100:0.02f}%)"
        profit_info = f"^ ${self.profit_cash:0.8f}, {self.profit_pct * 100:0.02f}% ^"
        return f"{price_info} {pos_info} {profit_info}"

    def __str__(self):
        return self.compact_display_str

    def __repr__(self):
        return self.compact_display_str


class GridGenerator(ABC):
    """
    网格生成器
    """

    @abstractmethod
    def generate(self) -> List[Level]:
        """
        产生网格

        Returns:
            网格格线列表
        """

    @abstractmethod
    def description(self) -> str:
        """
        文本描述

        Returns:
            描述
        """

    def export_json(self, path: Path):
        """
        将网格导出到 json 文件中
        Args:
            path (Path): json 文件路径
        """
        path.write_text(
            json.dumps(
                [(str(level.low_price), str(level.high_price), str(level.max_position)) for level in self.generate()],
                indent=2)
        )


class GridPositionManager:
    """
    网格
    """

    def __init__(self, generator: GridGenerator, level_min_profit: float = 0.005):
        """
        构造函数

        Args:
            generator (GridGenerator): 网格产生器
            level_min_profit (Decimal): 每格最小盈利率
        """
        self.generator = generator
        log.info(f"使用网格生成器生成网格: {generator.description()}")

        levels = generator.generate()
        self._check_levels(levels, level_min_profit)  # 检测网格是否合法
        self.levels = levels

    @staticmethod
    def _check_levels(levels: List[Level], min_profit: float):
        """
        检测网格合法性

        * 网格价格必须从高到低
        * 每个网格必须满足最小盈利率的要求

        Args:
            levels (List[Level]): 网格
            min_profit (Decimal): 最小盈利率

        Raises:
            RuntimeError
        """
        last_level_low_price = Decimal(MAX_EMAX)
        for level in levels:
            # 检测网格线是否正确
            if level.high_price > last_level_low_price:
                raise RuntimeError(f"非法网格，网格上线超过了上级网格的下线: {level}")

            if level.low_price >= level.high_price:
                raise RuntimeError(f"网格内最低、最高价非法：{level}")

            # 检测网格是否满足最小盈利率的要求
            if level.profit_pct < min_profit:
                raise RuntimeError(f"本网格不满足最小盈利率 {min_profit} 的要求: {level}")

            last_level_low_price = level.low_price

    def fill_positions(self, hold_position: Decimal, current_price: Decimal):
        """
        使用当前持有资产数量，和当前资产价格，填充网格

        Args:
            hold_position (Decimal): 持有资产数量
            current_price (Decimal): 当前资产价格
        Returns:
            资产（折算为现金）填充网格后的剩余的数量
        """
        assert hold_position >= 0
        for level in self.levels:  # 从价格最高顶到最低的格子级别
            if all([level.higher_than(current_price),  # 此格子在当前资产价格的上方
                    hold_position > 0,  # 当前资产的仓位还有剩余
                    level.remaining_position > 0  # 此格子还有剩余（未填充）仓位
                    ]):
                fill_pos = min(hold_position, level.remaining_position)
                level.inc_position(fill_pos)
                hold_position -= fill_pos
                if hold_position == 0:
                    break
        return hold_position

    def get_positions_to_buy(self, current_price: Decimal):
        """
        根据指定价格，获取可以购买的资产数量

        Args:
            current_price (Decimal): 当前价格

        Returns:
            可以购买的资产数量
        """
        total_positions = Decimal(0)
        for level in self.levels:
            if level.higher_than(current_price) and level.remaining_position > 0:
                # print(f"buying: {level}, {level.remaining_position}")
                total_positions += level.remaining_position
        return total_positions

    def get_positions_to_sell(self, current_price):
        """
        根据指定价格，获取可以卖出的资产数量

        Args:
            current_price (Decimal): 当前价格

        Returns:
            可以卖出的资产数量
        """
        total_positions = Decimal(0)
        for level in reversed(self.levels):
            if level.lower_than(current_price) and level.position > 0:
                # print(f"selling: {level.position}")
                total_positions += level.position
        return total_positions

    def bought_position(self, position: Decimal) -> Decimal:
        """
        更新买到的仓位数

        Args:
            position (Decimal): 买到的仓位数
        Returns:
            网格满仓（超出了网格容量的部分）后剩余的部分
        """
        for level in self.levels:
            if level.remaining_position > 0:
                fill_pos = min(position, level.remaining_position)
                level.inc_position(fill_pos)
                position -= fill_pos
        return position

    def sold_position(self, position: Decimal) -> Decimal:
        """
        更新卖出的仓位数

        Args:
            position (Decimal): 卖出仓位数

        Returns:
            网格空仓后（超出了网格容量的部分）后剩余的部分
        """
        for level in reversed(self.levels):  # 从价格低开始卖
            sold_pos = min(position, level.position)
            level.dec_position(sold_pos)
            position -= sold_pos
        return position

    def clear_positions(self):
        """
        清空持有仓位
        """
        for level in self.levels:
            level.position = 0

    @property
    def total_used_cash_qty(self):
        return sum([level.cash_qty for level in self.levels])

    @property
    def total_remaining_cash_qty(self):
        return sum([level.remaining_cash_qty for level in self.levels])

    @property
    def total_max_cash_qty(self):
        return sum([level.max_cash_qty for level in self.levels])

    @property
    def total_position(self):
        return sum([level.position for level in self.levels])

    @property
    def total_max_position(self):
        return sum([level.max_position for level in self.levels])

    @property
    def total_remaining_position(self):
        return sum([level.remaining_position for level in self.levels])

    @property
    def support_price(self):
        return self.levels[-1].low_price

    @property
    def resistance_price(self):
        return self.levels[0].high_price

    def log_levels(self):
        log.info(" LEVELS ".center(80, '*'))
        for i, level in enumerate(self.levels):
            log.info(f"{i}: {level}")

        log.info(f"网格资产：持仓 {self.total_position}，剩余：{self.total_remaining_position}，总容量：{self.total_max_position}")
        log.info(
            f"网格现金：已用 ${self.total_used_cash_qty}，剩余：${self.total_remaining_cash_qty}，总容量：${self.total_max_cash_qty}")
        log.info("*" * 80)

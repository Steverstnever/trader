from decimal import Decimal
from typing import List


# 数列生成函数

def create_geometric_sequence(size: int, common_ratio: float = 2) -> list:
    """创建等比数列"""
    assert size > 0 and common_ratio > 0
    return [common_ratio ** i for i in range(0, size)]


def create_arithmetic_sequence(size: int) -> list:
    """创建等差数列"""
    return [1] * size


def create_fibonacci_sequence(size: int) -> list:
    """创建斐波那契数列"""
    return [i for i in fibonacci_gen(size)]


def fibonacci_gen(count: int):
    """斐波那契数列生成器"""
    n, a, b = 0, 0, 1
    while n < count:
        yield b
        a, b = b, a + b
        n = n + 1


def grid_percents(g: list) -> list:
    """
    从格子数列计算每个格子的比例（占比）列表
    :param g: 格子数列
    :return: 格子占比数列
    """
    total = sum(g)
    return [i / total for i in g]


def grid_prices(low: Decimal, high: Decimal, grid: list) -> List[Decimal]:
    """
    计算价格网格

    :param low: 网格最低价格
    :param high:  网格最高价格
    :param grid: 格子数列
    :return: 价格网格
    """
    prices = [low, ]
    total = Decimal(sum(grid))
    sub_total = Decimal(0)
    for g in grid:
        sub_total += Decimal(g)
        prices.append(low + (high - low) * (sub_total / total))
    return prices

from decimal import Decimal
from typing import List, Callable


def is_ascending(items: List):
    """
    判断列表是否严格升序

    Args:
        items (list): 列表

    Returns:
        true 列表是严格升序的
    """
    return all([items[i] < items[i + 1] for i in range(len(items) - 1)])


def is_descending(items: List):
    """
    判断列表是否严格降序
    Args:
        items (list): 列表

    Returns:
        true 列表是严格降序的
    """
    return all([items[i] > items[i + 1] for i in range(len(items) - 1)])


def _equals(x, y, binary_op: Callable = None) -> bool:
    if binary_op is not None:
        return binary_op(x, y)
    else:
        return x == y


def is_constant(items: List, binary_op: Callable = None):
    """
    判断是否是常数数列
    Args:

        items (items): 列表
        binary_op (callable): 二元比较运算符，None 时代表是否 __eq__

    Returns:
        true 列表是常数数列
    """
    return all([_equals(items[i], items[i + 1], binary_op) for i in range(len(items) - 1)])


def arithmetic_ratio(low: Decimal, high: Decimal, current: Decimal) -> float:
    """
    计算算数比例

    公式：(current-low）/(high-low)
    Args:
        low (Decimal): 最低价
        high (Decimal): 最高价
        current (Decimal): 当前价

    Returns:
        算数比例

    Raises:
        decimal.DivisionByZero
    """
    return float((current - low) / (high - low))

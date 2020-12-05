from decimal import Decimal


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

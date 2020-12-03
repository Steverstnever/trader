from decimal import Decimal
from pathlib import Path

from trader.credentials import Credentials


def parse_decimal(s: str) -> Decimal:
    """
    解析字符串，生成正规化后的 Decimal

    >>> parse_decimal('5324.5000')
    Decimal('5324.5')
    >>> parse_decimal('5.3245E+3')
    Decimal('5324.5')

    Args:
        s (str): Decimal 的字符串

    Returns:
        正规化后的 Decimal
    """
    return normalize_decimal(Decimal(s))


def normalize_decimal(d: Decimal) -> Decimal:
    """
    去除 Decimal 中的科学计数法（比如：'5.3245E+3'）和尾巴的'0'

    >>> normalize_decimal(Decimal('5.3245E+3'))
    Decimal('5324.5')
    >>> normalize_decimal(Decimal('5E+3'))
    Decimal('5000')
    >>> normalize_decimal(Decimal('512.0001000'))
    Decimal('512.0001')
    >>> normalize_decimal(Decimal('5120001000'))
    Decimal('5120001000')
    
    Args:
        d (Decimal): 十进制表示的精度数字

    Returns:
        正规化（去除指数和尾随'0'）的十进制表示的精度数字
    """
    return d.quantize(Decimal(1)) if d == d.to_integral() else d.normalize()


def project_root() -> Path:
    """
    返回项目根路径
    """
    return Path(__file__).parent.parent


def load_dev_credentials() -> Credentials:
    """
    开发时装载用户凭证
    """
    credentials_path = project_root() / '.local/credentials.json'
    if not credentials_path.exists():
        raise RuntimeError(f"【错误】用户凭证文件不存在: {credentials_path}")

    return Credentials.load_from_json(credentials_path)

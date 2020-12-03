from decimal import Decimal

from trader import utils


def test_parse_decimal():
    assert utils.parse_decimal('5324.5000') == Decimal('5324.5')
    assert utils.parse_decimal('5.3245E+3') == Decimal('5324.5')
    assert utils.parse_decimal('0.0050') == Decimal('0.005')
    assert utils.parse_decimal('100.') == Decimal('100')
    assert utils.parse_decimal('100.00') == Decimal('100')
    assert utils.parse_decimal('-5322.123000') == Decimal('-5322.123')


def test_normalize_decimal():
    assert utils.normalize_decimal(Decimal('5.3245E+3')) == Decimal('5324.5')
    assert utils.normalize_decimal(Decimal('5E+3')) == Decimal('5000')
    assert utils.normalize_decimal(Decimal('512.0001000')) == Decimal('512.0001')
    assert utils.normalize_decimal(Decimal('5120001000')) == Decimal('5120001000')

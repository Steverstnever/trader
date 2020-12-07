import math
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


def test_ordering():
    assert utils.is_ascending([1, 2, 3, 4, 5])
    assert utils.is_descending([5, 4, 3, 2, 1])
    assert not utils.is_ascending([1, 2, 4, 3, 5]) and not utils.is_descending([1, 2, 4, 3, 5])

    assert utils.is_constant([2, 2, 2])
    assert utils.is_constant([12.0, 12.0, 12.0], math.isclose)

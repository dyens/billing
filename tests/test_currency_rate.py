from decimal import Decimal

import pytest

from billing.currency_rate.currency_rate import get_currency_rate


def test_get_currency_rate():
    """Test get currency rate mock adapter."""
    assert round(get_currency_rate('USD'), 4) == Decimal('1')
    assert round(get_currency_rate('EUR'), 4) == Decimal('1.1532')
    assert round(get_currency_rate('CAD'), 4) == Decimal('0.7862')
    assert round(get_currency_rate('CNY'), 4) == Decimal('0.1468')

    with pytest.raises(ValueError):
        get_currency_rate('UNKNOWN_VALUE')

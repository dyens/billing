"""Currency rate adapter."""

import random
from decimal import Decimal

from dynaconf import settings


def get_currency_rate(currency_name: str) -> Decimal:
    """Currency rate.

    Return random currency rate to USD base
    """
    # default currency rates
    default_currencies = {
        'USD': 1,
        'EUR': 1.1,
        'CAD': 0.75,
        'CNY': 0.14,
    }

    if currency_name not in default_currencies:
        raise ValueError('Unknown currency')

    if currency_name == 'USD':
        return Decimal('1')

    default_currency = default_currencies[currency_name]

    # Its not suitable for security, but its mock function...
    random.seed(settings.RANDOM_SEED)  # NOQA:S311
    currency = default_currency * random.uniform(1.0, 1.05)  # NOQA:S311
    return Decimal(currency)

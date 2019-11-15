from decimal import Decimal
from typing import Tuple

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import select

from billing.db.models import (
    Currency,
    user,
    wallet,
)


async def create_new_user(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    name: str,
    country: str,
    city: str,
    currency: Currency,
    balance: Decimal,
) -> Tuple[int, int]:
    """Create new user with wallet.

    :return: (new user_id,  new wallet_id)
    """
    if balance < 0:
        raise ValueError('Balance must be positive')
    create_user_query = user.insert().values(
        name=name,
        country=country,
        city=city,
    ).returning(user.c.id)
    new_user_record = await conn.fetchrow(create_user_query)
    new_user_id: int = new_user_record['id']
    create_wallet_query = wallet.insert().values(
        user_id=new_user_id,
        balance=balance,
        currency=currency,
    ).returning(wallet.c.id)
    new_wallet_record = await conn.fetchrow(create_wallet_query)
    new_wallet_id: int = new_wallet_record['id']
    return (new_user_id, new_wallet_id)


async def get_user_info(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    user_id: int,
):
    """User info."""
    user_info_query = select(
        [
            user.c.name,
            user.c.country,
            user.c.city,
            wallet.c.balance,
            wallet.c.currency,
        ],
    ).select_from(
        user.join(wallet),
    ).where(
        user.c.id == user_id,
    )

    user_info_record = await conn.fetchrow(user_info_query)
    if user_info_record is None:
        raise ValueError('Unknown user.')
    return {
        'name': user_info_record['name'],
        'city': user_info_record['city'],
        'country': user_info_record['country'],
        'balance': user_info_record['balance'],
        'currency': user_info_record['currency'],
    }

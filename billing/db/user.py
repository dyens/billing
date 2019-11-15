from decimal import Decimal
from typing import Tuple

from asyncpg.pool import PoolConnectionProxy

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

from decimal import Decimal
from typing import (
    Dict,
    List,
    Optional,
)

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import (
    exists,
    select,
)
from sqlalchemy.sql.schema import Column as ColumnType

from billing.db.exceptions import WalletDoesNotExists
from billing.db.models import wallet


async def is_wallet_exists(
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
) -> bool:
    """Existing wallet."""
    wallet_exists_query = select([exists().where(wallet.c.id == wallet_id)])
    wallet_exists: bool = await conn.fetchval(wallet_exists_query)
    return wallet_exists  # NOQA:WPS331


async def get_wallet_info(
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    columns: Optional[List[ColumnType]] = None,
):
    """Get wallet info."""
    if columns is None:
        wallet_info = await conn.fetchrow(
            wallet.select().where(wallet.c.id == wallet_id),
        )
    else:
        wallet_info = await conn.fetchrow(
            select(columns).select_from(
                wallet,
            ).where(
                wallet.c.id == wallet_id,
            ),
        )
    if wallet_info is not None:
        wallet_info_dict: Optional[Dict] = dict(wallet_info)
    else:
        wallet_info_dict = None
    return wallet_info_dict  # NOQA:WPS331


async def add_to_wallet(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    amount: Decimal,
) -> Decimal:
    """Wallet top up."""
    if amount < 0:
        raise ValueError('Amount must be positive')
    wallet_exists = await is_wallet_exists(
        conn,
        wallet_id=wallet_id,
    )
    if wallet_exists is False:
        raise WalletDoesNotExists('Wallet does not exists')
    wallet_update_query = wallet \
        .update() \
        .where(wallet.c.id == wallet_id) \
        .values(balance=wallet.c.balance + amount) \
        .returning(wallet.c.balance)
    new_balance_record = await conn.fetchrow(wallet_update_query)
    new_balance: Decimal = new_balance_record['balance']
    return new_balance  # NOQA:WPS331


async def get_from_wallet(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    amount: Decimal,
) -> Decimal:
    """Get money from wallet."""
    if amount < 0:
        raise ValueError('Amount must be positive')
    wallet_exists = await is_wallet_exists(
        conn,
        wallet_id=wallet_id,
    )
    if wallet_exists is False:
        raise WalletDoesNotExists('Wallet does not exists')
    wallet_update_query = wallet \
        .update() \
        .where(wallet.c.id == wallet_id) \
        .values(balance=wallet.c.balance - amount) \
        .returning(wallet.c.balance)
    new_balance_record = await conn.fetchrow(wallet_update_query)
    new_balance: Decimal = new_balance_record['balance']
    return new_balance  # NOQA:WPS331

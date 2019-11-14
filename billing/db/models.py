"""Models."""

import enum
from decimal import Decimal
from typing import Tuple

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    exists,
    select,
)
from sqlalchemy.sql import func

from billing.db.exceptions import WalletDoesNotExists

metadata = MetaData()

# User table
user = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column('name', String, nullable=False),
    Column('country', String, nullable=False),
    Column('city', String, nullable=False),
)


@enum.unique
class Currency(enum.Enum):
    """Available Currencies."""

    USD = 'USD'
    EUR = 'EUR'
    CAD = 'CAD'
    CNY = 'CNY'


# User wallet table
wallet = Table(
    'wallet',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column(
        'user_id',
        Integer,
        ForeignKey(
            'user.id',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        nullable=False,
    ),
    Column('balance', Numeric, nullable=False, default=Decimal(0.0)),
    Column('currency', Enum(Currency), nullable=False, default=Currency.USD),
    CheckConstraint('balance >= 0', name='positive_balance'),
)


@enum.unique
class TransactionState(enum.Enum):
    """Transaction states beetwen wallets."""

    CREATED = enum.auto()
    SUCCESED = enum.auto()
    FAILED = enum.auto()


class FailedReason(enum.Enum):
    """Failed reasons."""

    # NEM - not enough money
    NEM_FROM_WALLET = enum.auto()
    # Currencies api not available
    CUR_API_NA = enum.auto()
    # Some unknown errors
    UNKNOWN = enum.auto()


# Table of transactions beetween wallets
transaction = Table(
    'transaction',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column(
        'from_wallet_id',
        Integer,
        ForeignKey(
            'wallet.id',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        nullable=False,
    ),
    Column(
        'to_wallet_id',
        Integer,
        ForeignKey(
            'wallet.id',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        nullable=False,
    ),
    Column('state', Enum(TransactionState), nullable=False),
    Column('amount', Numeric, nullable=False),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
    Column('updated_at', DateTime, nullable=False, onupdate=func.now()),
    Column('exchange_rate', Numeric),
    Column('failed_reason', Enum(FailedReason)),
)

# Transaction log table
transaction_log = Table(
    'transaction_log',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column(
        'transaction_id',
        Integer,
        ForeignKey(
            'transaction.id',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        nullable=False,
    ),
    Column('state', Enum(TransactionState), nullable=False),
    Column('comment', Text),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
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
    if not isinstance(balance, Decimal):
        raise ValueError('Wrong type of balance')
    if balance < 0:
        raise ValueError('Balance must be positive')
    async with conn.transaction():
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


async def add_to_wallet(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    quantity: Decimal,
) -> Decimal:
    """Wallet top up."""
    if not isinstance(quantity, Decimal):
        raise ValueError('Wrong type of quantity')
    if quantity < 0:
        raise ValueError('Quantity must be positive')
    async with conn.transaction():
        wallet_exists_query = select([exists().where(wallet.c.id == wallet_id)])
        wallet_exists = await conn.fetchval(wallet_exists_query)
        if not wallet_exists:
            raise WalletDoesNotExists('Wallet does not exist')
        wallet_update_query = wallet \
            .update() \
            .where(wallet.c.id == wallet_id) \
            .values(balance=wallet.c.balance + quantity) \
            .returning(wallet.c.balance)
        new_balance_record = await conn.fetchrow(wallet_update_query)
        new_balance: Decimal = new_balance_record['balance']
        return new_balance  # NOQA:WPS331

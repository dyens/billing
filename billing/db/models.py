"""Models."""

import enum
from decimal import Decimal

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import (
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
    select,
)
from sqlalchemy.sql import func

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


class Currency(enum.Enum):
    """Available Currencies."""

    USD = enum.auto()
    EUR = enum.auto()
    CAD = enum.auto()
    CNY = enum.auto()


# User wallet table
wallet = Table(
    'wallet',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('balance', Numeric, nullable=False, default=Decimal(0.0)),
    Column('currency', Enum(Currency), nullable=False, default=Currency.USD),
)


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


# Table of transactions beetwetn wallets
transaction = Table(
    'transaction',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column('from_wallet_id', Integer, ForeignKey('wallet.id')),
    Column('to_wallet_id', Integer, ForeignKey('wallet.id')),
    Column('state', Enum(TransactionState), nullable=False),
    Column('amount', Numeric, nullable=False),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
    Column('updated_at', DateTime, nullable=False, onupdate=func.now()),
    Column('exchange_rate', Numeric),
    Column('failed_reason', Enum(FailedReason)),
)

# Table of transactions beetwetn wallets
transaction_log = Table(
    'transaction_log',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column('transaction_id', Integer, ForeignKey('transaction.id')),
    Column('state', Enum(TransactionState), nullable=False),
    Column('comment', Text),
    Column('created_at', DateTime, nullable=False, server_default=func.now()),
)


async def get_users(conn: PoolConnectionProxy) -> str:
    """Get all users."""
    query = select([
        user.c.id,
    ]).select_from(user)
    users = await conn.fetch(query)
    return str(users)


async def get_wallets(conn: PoolConnectionProxy) -> str:
    """Get all wallets."""
    query = select([
        wallet.c.id,
    ]).select_from(wallet)
    wallets = await conn.fetch(query)
    return str(wallets)

"""Models."""

import enum
from decimal import Decimal

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
    Column(
        'updated_at',
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),

    Column('new_balance_from', Numeric),
    Column('new_balance_to', Numeric),
    Column('exchange_from_rate', Numeric),
    Column('exchange_to_rate', Numeric),
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

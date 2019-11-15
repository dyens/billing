"""Models."""

import enum
from decimal import Decimal
from typing import (
    List,
    Optional,
    Tuple,
)

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
from sqlalchemy.sql.schema import Column as ColumnType

from billing.currency_rate.currency_rate import get_currency_rate
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
    Column(
        'updated_at',
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
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


async def is_wallet_exists(
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
) -> bool:
    wallet_exists_query = select([exists().where(wallet.c.id == wallet_id)])
    return await conn.fetchval(wallet_exists_query)


async def get_wallet_info(
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    columns: Optional[List[ColumnType]] = None,
) -> dict:
    """Get wallet info."""
    if columns is None:
        info = await conn.fetchrow(
            wallet.select().where(wallet.c.id == wallet_id)
        )
    else:
        info = await conn.fetchrow(
            select(columns).select_from(wallet).where(
                wallet.c.id == wallet_id
            )
        )
    if info is not None:
        info = dict(info)
    return info



async def add_to_wallet(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    wallet_id: int,
    amount: Decimal,
) -> Decimal:
    """Wallet top up."""
    if amount < 0:
        raise ValueError('Amount must be positive')
    if await is_wallet_exists(
        conn,
        wallet_id=wallet_id,
    ) is False:
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
    if await is_wallet_exists(
        conn,
        wallet_id=wallet_id,
    ) is False:
        raise WalletDoesNotExists('Wallet does not exists')
    wallet_update_query = wallet \
        .update() \
        .where(wallet.c.id == wallet_id) \
        .values(balance=wallet.c.balance - amount) \
        .returning(wallet.c.balance)
    new_balance_record = await conn.fetchrow(wallet_update_query)
    new_balance: Decimal = new_balance_record['balance']
    return new_balance  # NOQA:WPS331


async def add_transaction_log(
    conn: PoolConnectionProxy,
    *,
    transaction_id: int,
    state: TransactionState,
    comment: str,
) -> None:
    """Add log to transaction"""
    create_log_query = transaction_log.insert().values(
        transaction_id=transaction_id,
        state=state,
        comment=comment,
    )
    await conn.execute(create_log_query)


async def create_transaction(
    conn: PoolConnectionProxy,
    *,
    from_wallet_id: int,
    to_wallet_id: int,
    amount: Decimal,
) -> int:
    """Create new transaction."""
    if from_wallet_id == to_wallet_id:
        raise ValueError('Cant transfer yourself')
    create_transaction_query = transaction.insert().values(
        from_wallet_id=from_wallet_id,
        to_wallet_id=to_wallet_id,
        state=TransactionState.CREATED,
        amount=amount,
    ).returning(transaction.c.id)
    new_transaction_record = await conn.fetchrow(create_transaction_query)
    new_transaction_id = new_transaction_record['id']
    await add_transaction_log(
        conn,
        transaction_id=new_transaction_id,
        state=TransactionState.CREATED,
        comment='Transaction created',
    )
    return new_transaction_id


async def fail_transaction(
    conn: PoolConnectionProxy,
    *,
    transaction_id: int,
    reason: FailedReason,
    comment: str,
):
    """Set transaction to failed."""
    await add_transaction_log(
        conn,
        transaction_id=transaction_id,
        state=TransactionState.FAILED,
        comment=comment,
    )

    update_transaction_query = transaction \
        .update() \
        .where(transaction.c.id == transaction_id) \
        .values(
            failed_reason=reason,
            state=TransactionState.FAILED,
        )
    await conn.execute(update_transaction_query)


async def success_transaction(
    conn: PoolConnectionProxy,
    *,
    transaction_id: int,
    exchange_from_rate: Decimal,
    exchange_to_rate: Decimal,
    comment: str,
):
    """Set transaction to success."""
    await add_transaction_log(
        conn,
        transaction_id=transaction_id,
        state=TransactionState.SUCCESED,
        comment=comment,
    )

    update_transaction_query = transaction \
        .update() \
        .where(transaction.c.id == transaction_id) \
        .values(
            exchange_from_rate=exchange_from_rate,
            exchange_to_rate=exchange_to_rate,
            state=TransactionState.SUCCESED,
        )
    await conn.execute(update_transaction_query)


async def validate_transaction(
    conn: PoolConnectionProxy,
    *,
    transaction_id: int,
) -> bool:
    """Check transaction valid.
    
    In demo case we check that balance > transfer amount.
    """

    transaction_info_query = select(
        [
            transaction.c.amount,
            wallet.c.balance,
        ]
    ).select_from(
        transaction.join(
            wallet,
            transaction.c.from_wallet_id == wallet.c.id,
        ),
    ).where(transaction.c.id == transaction_id)
    transaction_info_record = await conn.fetchrow(transaction_info_query)
    amount = transaction_info_record['amount']
    balance = transaction_info_record['balance']
    if amount > balance:
        await fail_transaction(
            conn,
            transaction_id=transaction_id,
            reason=FailedReason.NEM_FROM_WALLET,
            comment='Not enough balance',
        )
        return False
    return True


async def transfer_between_wallets(  # NOQA:WPS211
    conn: PoolConnectionProxy,
    *,
    from_wallet_id: int,
    to_wallet_id: int,
    amount: Decimal,
) -> None:
    """Transfer betwen wallets."""
    if not isinstance(amount, Decimal):
        raise ValueError('Wrong type of amount')
    if amount < 0:
        raise ValueError('Amount must be positive')
    async with conn.transaction():
        # 1. first check wallets exists
        # This check need be duplicated in api
        for wallet_id in (from_wallet_id, to_wallet_id):
            if await is_wallet_exists(conn, wallet_id=wallet_id) is False:
                raise WalletDoesNotExists(
                    'Wallet {wallet_id} does not exist'.format(
                        wallet_id=wallet_id
                    ),
                )

        # 2. Create transaction
        transaction_id = await create_transaction(
            conn,
            from_wallet_id=from_wallet_id,
            to_wallet_id=to_wallet_id,
            amount=amount,
        )

        # 3. Validate transaction
        if await validate_transaction(
            conn,
            transaction_id=transaction_id,
        ) is False:
            return

        # 4. Get currency rate
        wallet_from_info = await get_wallet_info(
            conn,
            wallet_id=from_wallet_id,
            columns=[wallet.c.currency],
        )
        wallet_from_currency = wallet_from_info['currency']
        exchange_from_rate = await get_currency_rate(wallet_from_currency)

        wallet_to_info = await get_wallet_info(
            conn,
            wallet_id=to_wallet_id,
            columns=[wallet.c.currency],
        )
        wallet_to_currency = wallet_to_info['currency']
        exchange_to_rate = await get_currency_rate(wallet_to_currency)

        add_amount = amount * exchange_from_rate / exchange_to_rate

        # 5. Transfer money
        await get_from_wallet(
            conn,
            wallet_id=from_wallet_id,
            amount=amount,
        )
        await add_to_wallet(
            conn,
            wallet_id=to_wallet_id,
            amount=add_amount,
        )

        # 6. Success
        await success_transaction(
            conn,
            transaction_id=transaction_id,
            exchange_from_rate=exchange_from_rate,
            exchange_to_rate=exchange_to_rate,
            comment='Success',
        )

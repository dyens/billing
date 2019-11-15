from decimal import Decimal

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import select

from billing.currency_rate.currency_rate import get_currency_rate
from billing.db.exceptions import WalletDoesNotExists
from billing.db.models import (
    FailedReason,
    TransactionState,
    transaction,
    transaction_log,
    wallet,
)
from billing.db.wallet import (
    add_to_wallet,
    get_from_wallet,
    get_wallet_info,
    is_wallet_exists,
)


async def add_transaction_log(
    conn: PoolConnectionProxy,
    *,
    transaction_id: int,
    state: TransactionState,
    comment: str,
) -> None:
    """Add log to transaction."""
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
    new_transaction_id: int = new_transaction_record['id']
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
        ],
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
                        wallet_id=wallet_id,
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
        is_valid = await validate_transaction(
            conn,
            transaction_id=transaction_id,
        )
        if is_valid is False:
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

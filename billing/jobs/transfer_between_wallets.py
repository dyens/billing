from billing.db.setup import create_pool
from billing.db.transaction import transfer_between_wallets


async def transfer_between_wallets_job(
    *,
    from_wallet_id,
    to_wallet_id,
    amount,
):
    """Transfer between wallets job."""
    pool = await create_pool()

    try:  # NOQA: WPS501
        async with pool.acquire() as conn:
            await transfer_between_wallets(
                conn,
                from_wallet_id=from_wallet_id,
                to_wallet_id=to_wallet_id,
                amount=amount,
            )
    finally:
        await pool.close()

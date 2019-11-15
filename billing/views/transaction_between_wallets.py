from contextlib import AsyncExitStack

from aiohttp import web
from aiohttp.web import Response
from aiohttp.web_request import Request
from aiohttp_apispec import (
    docs,
    request_schema,
)
from aiojobs.aiohttp import spawn
from marshmallow import (
    Schema,
    fields,
)
from marshmallow.validate import Range

from billing.db.wallet import is_wallet_exists
from billing.jobs.transfer_between_wallets import transfer_between_wallets_job


class TransactionBetweenWalletsRequestSchema(Schema):
    """Request schema."""

    from_wallet_id = fields.Int(description='from_wallet_id', required=True)
    to_wallet_id = fields.Int(description='to_wallet_id', required=True)
    amount = fields.Decimal(
        description='amount',
        required=True,
        validate=[
            Range(min=0, error='Negative amount.'),
        ],
    )


class TransactionBetweenWalletsResponseSchema(Schema):
    """Response schema."""

    # Decimal is not json serializable.
    # Dont whant to deal with its.
    msg = fields.Str()


@docs(
    tags=['Transaction'],
    summary='Transaction between wallets',
    description='Transaction between wallets',
    responses={
        200: {
            'schema': TransactionBetweenWalletsResponseSchema,
            'description': 'Success response',
        },
        404: {
            'description': 'Wallet does not exists',
        },
        422: {
            'description': 'Validation error',
        },
    },
)
@request_schema(TransactionBetweenWalletsRequestSchema())
async def transaction_between_wallets(request: Request) -> Response:
    """Wallet top up."""
    request_data = request['data']
    from_wallet_id = request_data['from_wallet_id']
    to_wallet_id = request_data['to_wallet_id']
    amount = request_data['amount']

    if from_wallet_id == to_wallet_id:
        raise web.HTTPUnprocessableEntity(reason='Transfer yourself')

    # First check wallet exists.
    async with AsyncExitStack() as with_stack:
        conn = await with_stack.enter_async_context(
            request.app['db'].acquire(),
        )
        await with_stack.enter_async_context(conn.transaction())

        for wallet_id in (from_wallet_id, to_wallet_id):
            if await is_wallet_exists(conn, wallet_id=wallet_id) is False:
                return web.HTTPNotFound(
                    reason='Wallet {wallet_id} does not exist'.format(
                        wallet_id=wallet_id,
                    ),
                )

    # Then create trasaction.
    await spawn(
        request,
        transfer_between_wallets_job(
            from_wallet_id=from_wallet_id,
            to_wallet_id=to_wallet_id,
            amount=amount,
        ),
    )
    return web.json_response({'msg': 'Transaction created'})

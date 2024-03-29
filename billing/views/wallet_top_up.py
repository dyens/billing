from contextlib import AsyncExitStack

from aiohttp import web
from aiohttp.web import Response
from aiohttp.web_request import Request
from aiohttp_apispec import (
    docs,
    request_schema,
)
from marshmallow import (
    Schema,
    fields,
)
from marshmallow.validate import Range

from billing.db.exceptions import WalletDoesNotExists
from billing.db.wallet import add_to_wallet


class WalletTopUpRequestSchema(Schema):
    """Request wallet top up schema."""

    wallet_id = fields.Int(description='wallet_id', required=True)
    amount = fields.Decimal(
        description='amount',
        required=True,
        validate=[
            Range(min=0, error='Negative amount.'),
        ],
    )


class WalletTopUpResponseSchema(Schema):
    """Response register user schema."""

    # Decimal is not json serializable.
    # Dont whant to deal with its.
    new_balance = fields.Str()


@docs(
    tags=['Wallet'],
    summary='Wallet top up',
    description='Add to wallet',
    responses={
        200: {
            'schema': WalletTopUpResponseSchema,
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
@request_schema(WalletTopUpRequestSchema())
async def wallet_top_up(request: Request) -> Response:
    """Wallet top up."""
    request_data = request['data']
    async with AsyncExitStack() as with_stack:
        conn = await with_stack.enter_async_context(
            request.app['db'].acquire(),
        )
        await with_stack.enter_async_context(conn.transaction())
        try:
            new_user_balance = await add_to_wallet(
                conn,
                wallet_id=request_data['wallet_id'],
                amount=request_data['amount'],
            )
        except WalletDoesNotExists:
            return web.HTTPNotFound(reason='Wallet does not exists')
    return web.json_response({'new_balance': str(new_user_balance)})

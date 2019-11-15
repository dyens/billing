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

from billing.db.transaction import transfers_history
from billing.db.wallet import is_wallet_exists


class TransactionsHistoryRequestSchema(Schema):
    """Request transactions history schema."""

    wallet_id = fields.Int(description='wallet_id', required=True)
    start = fields.DateTime(description='start')
    end = fields.DateTime(description='end')


class TransactionsHistoryRecord(Schema):
    """Transaction histryo record."""

    transaction_id = fields.Int(description='transaction_id')
    wallet_from = fields.Int(description='wallet_from')
    wallet_to = fields.Int(description='wallet_to')
    amount = fields.Str(description='amount')
    new_balance = fields.Str(description='new_balance')
    created = fields.DateTime(description='created')
    state = fields.Str(description='state')


class TransactionsHistoryResponseSchema(Schema):
    """Response transactions history schema."""

    history = fields.Nested(TransactionsHistoryRecord)


@docs(
    tags=['Transaction'],
    summary='Transactions history',
    description='Transactions history',
    responses={
        200: {
            'schema': TransactionsHistoryResponseSchema,
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
@request_schema(TransactionsHistoryRequestSchema())
async def transactions_history(request: Request) -> Response:
    """Transactions history."""
    request_data = request['data']
    wallet_id = request_data['wallet_id']
    start = request_data.get('start')
    end = request_data.get('end')
    async with AsyncExitStack() as with_stack:
        conn = await with_stack.enter_async_context(
            request.app['db'].acquire(),
        )
        await with_stack.enter_async_context(conn.transaction())
        wallet_exist = await is_wallet_exists(conn, wallet_id=wallet_id)
        if wallet_exist is False:
            return web.HTTPNotFound(reason='Wallet does not exists')
        history = await transfers_history(
            conn,
            wallet_id=wallet_id,
            start=start,
            end=end,
        )
    return web.json_response({'history': history})

from contextlib import AsyncExitStack

from aiohttp import web
from aiohttp.web import Response
from aiohttp.web_request import Request
from aiohttp_apispec import docs
from marshmallow import (
    Schema,
    fields,
)

from billing.db.transaction import get_transaction_logs


class TransactionsLogRecord(Schema):
    """Transaction log record."""

    comment = fields.Str(description='comment')
    created = fields.DateTime(description='created')
    state = fields.Str(description='state')


class TransactionLogsResponseSchema(Schema):
    """Response transaction logs schema."""

    logs = fields.Nested(TransactionsLogRecord)


@docs(
    tags=['Transaction'],
    summary='Transaction logs',
    description='Transaction logs',
    responses={
        200: {
            'schema': TransactionLogsResponseSchema,
            'description': 'Success response',
        },
        404: {
            'description': 'Unknown transaction',
        },
    },
)
async def transaction_logs(request: Request) -> Response:
    """Transactions logs."""
    transaction_id = request.match_info['transaction_id']
    transaction_id = int(transaction_id)
    async with AsyncExitStack() as with_stack:
        conn = await with_stack.enter_async_context(
            request.app['db'].acquire(),
        )
        await with_stack.enter_async_context(conn.transaction())
        logs = await get_transaction_logs(
            conn,
            transaction_id=transaction_id,
        )
    return web.json_response({'logs': logs})

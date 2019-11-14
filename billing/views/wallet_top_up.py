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

from billing.db.exceptions import UserDoesNotExists
from billing.db.models import add_to_wallet


class WalletTopUpRequestSchema(Schema):
    """Request wallet top up schema."""

    user_id = fields.Int(description='user_id', required=True)
    quantity = fields.Decimal(
        description='balance',
        required=True,
        validate=[
            Range(min=0, error='Negative quantity.'),
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
            'description': 'User not found',
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
    async with request.app['db'].acquire() as conn:
        try:
            new_user_balance = await add_to_wallet(
                conn,
                user_id=request_data['user_id'],
                quantity=request_data['quantity'],
            )
        except UserDoesNotExists:
            return web.HTTPNotFound(reason='User does not exists')
    return web.json_response({'new_balance': str(new_user_balance)})

from decimal import Decimal

from aiohttp import web
from aiohttp.web import Response
from aiohttp.web_request import Request
from aiohttp_apispec import (
    docs,
    request_schema,
    response_schema,
)
from marshmallow import (
    Schema,
    fields,
)
from marshmallow.validate import Range
from marshmallow_enum import EnumField

from billing.db.models import (
    Currency,
    create_new_user,
)


class UserRegisterRequestSchema(Schema):
    """Request register user schema."""

    name = fields.Str(description='name', required=True)
    country = fields.Str(description='country', required=True)
    city = fields.Str(description='city', required=True)
    balance = fields.Decimal(
        description='balance',
        required=False,
        validate=[
            Range(min=0, error='Negative balance.'),
        ],
    )
    currency = EnumField(Currency, description='currency_type', required=True)


class UserRegisterResponseSchema(Schema):
    """Response register user schema."""

    new_user_id = fields.Int()
    new_wallet_id = fields.Int()


@docs(
    tags=['User'],
    summary='Create new user',
    description='New user registration',
)
@request_schema(UserRegisterRequestSchema())
@response_schema(UserRegisterResponseSchema())
async def user_register(request: Request) -> Response:
    """Register new user."""
    request_data = request['data']
    balance = request_data.get('balance')
    if balance is None:
        balance = Decimal(0.0)
    async with request.app['db'].acquire() as conn:
        new_user_id, new_wallet_id = await create_new_user(
            conn,
            name=request_data['name'],
            country=request_data['country'],
            city=request_data['city'],
            currency=request_data['currency'],
            balance=balance,
        )
    return web.json_response(
        {
            'new_user_id': new_user_id,
            'new_wallet_id': new_wallet_id,
        },
    )

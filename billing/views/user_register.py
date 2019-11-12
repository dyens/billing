from decimal import Decimal

from aiohttp import web
from aiohttp_apispec import (
    docs,
    request_schema,
)
from marshmallow import (
    Schema,
    fields,
)
from marshmallow_enum import EnumField

from billing.db.models import (
    Currency,
    create_new_user,
)


class RequestSchema(Schema):
    """Request register user schema."""

    name = fields.Str(description='name', required=True)
    country = fields.Str(description='country', required=True)
    city = fields.Str(description='city', required=True)
    balance = fields.Int(description='balance', required=False)
    currency = EnumField(Currency, description='currency_type', required=True)


class ResponseSchema(Schema):
    """Response register user schema."""

    msg = fields.Str()


@docs(
    tags=['User'],
    summary='Create new user',
    description='New user registration',
)
@request_schema(RequestSchema())
async def user_register(request):
    """Register new user."""
    request_data = request['request_data']
    balance = request_data.get('balance')
    if balance is None:
        balance = Decimal(0.0)
    async with request.app['db'].acquire() as conn:
        new_user_id = await create_new_user(
            conn,
            name=request_data['name'],
            country=request_data['country'],
            city=request_data['city'],
            currency=request_data['currency'],
            balance=balance,
        )
    return web.json_response({'msg': new_user_id})

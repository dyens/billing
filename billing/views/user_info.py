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

from billing.db.user import get_user_info


class UserInfoRequestSchema(Schema):
    """Request user info schema."""

    user_id = fields.Int(description='user_id', required=True)


class UserInfoResponseSchema(Schema):
    """Response user info schema."""

    name = fields.Str()
    city = fields.Str()
    country = fields.Str()
    balance = fields.Str()
    currency = fields.Str()


@docs(
    tags=['User'],
    summary='User info',
    description='User info',
    responses={
        200: {
            'schema': UserInfoResponseSchema,
            'description': 'Success response',
        },
        404: {
            'description': 'User does not exists',
        },
        422: {
            'description': 'Validation error',
        },
    },
)
@request_schema(UserInfoRequestSchema())
async def user_info(request: Request) -> Response:
    """User info."""
    request_data = request['data']
    user_id = request_data['user_id']
    async with AsyncExitStack() as with_stack:
        conn = await with_stack.enter_async_context(
            request.app['db'].acquire(),
        )
        await with_stack.enter_async_context(conn.transaction())

        try:
            user_data = await get_user_info(conn, user_id=user_id)
        except ValueError:
            raise web.HTTPNotFound(reason='User does not exists')
    user_data['balance'] = str(user_data['balance'])
    return web.json_response(user_data)

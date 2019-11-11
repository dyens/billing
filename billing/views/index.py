from aiohttp import web
from billing.db import get_users


async def index(request):
    async with request.app['db'].acquire() as conn:
        res = await get_users(conn)

    return web.Response(text=str(res))

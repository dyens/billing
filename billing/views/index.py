from aiohttp.web import Response
from aiohttp.web_request import Request

from billing.db.models import get_users


async def index(request: Request) -> Response:
    """Generate index page."""
    async with request.app['db'].acquire() as conn:
        res = await get_users(conn)
    return Response(text=str(res))

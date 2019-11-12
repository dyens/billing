from aiohttp.web import Response
from aiohttp.web_request import Request


async def index(request: Request) -> Response:
    """Generate index page."""
    return Response(text='hello world')

from aiohttp.web_app import Application

from billing.views import index


def setup_routes(app: Application) -> None:
    """Add routes to app."""
    app.router.add_get('/', index.index)

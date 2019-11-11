from aiohttp import web
from aiohttp.web_app import Application
from dynaconf import settings

from billing.db.setup import (
    close_pg,
    init_pg,
)
from billing.routes import setup_routes


async def init_app() -> Application:
    """Init app."""
    app = web.Application()
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)

    # setup views and routes
    setup_routes(app)
    return app


if __name__ == '__main__':
    app = init_app()
    web.run_app(app, host=settings.HOST, port=settings.PORT)

import logging
import sys

from dynaconf import settings
from aiohttp import web

from billing.db import close_pg, init_pg
from billing.routes import setup_routes


async def init_app():

    app = web.Application()

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)

    # setup views and routes
    setup_routes(app)
    return app


logging.basicConfig(level=logging.DEBUG)
app = init_app()
web.run_app(app,
        host=settings.HOST,
        port=settings.PORT)



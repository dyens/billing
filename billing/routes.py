from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec

from billing.views import (
    index,
    user_register,
)


def setup_routes(app: Application) -> None:
    """Add routes to app."""
    app.router.add_get('/', index.index, allow_head=False)
    # TODO: add version /v1/user_register
    app.router.add_post('/user_register', user_register.user_register)

    setup_aiohttp_apispec(
        app=app,
        title='My Documentation',
        version='v1',
        url='/api/docs/swagger.json',
        swagger_path='/api/docs',
    )

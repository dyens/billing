from aiohttp.web_app import Application
from aiohttp_apispec import setup_aiohttp_apispec

from billing.views import (
    transaction_between_wallets,
    transaction_logs,
    transactions_history,
    user_info,
    user_register,
    wallet_top_up,
)


def setup_routes(app: Application) -> None:
    """Add routes to app."""
    app.router.add_post('/v1/user_register', user_register.user_register)
    app.router.add_post('/v1/user_info', user_info.user_info)
    app.router.add_post('/v1/wallet_top_up', wallet_top_up.wallet_top_up)
    app.router.add_post(
        '/v1/transaction_between_wallets',
        transaction_between_wallets.transaction_between_wallets,
    )

    app.router.add_post(
        '/v1/transactions_history',
        transactions_history.transactions_history,
    )

    app.router.add_get(
        r'/v1/transaction_logs/{transaction_id:\d+}',
        transaction_logs.transaction_logs,
        allow_head=False,
    )

    setup_aiohttp_apispec(
        app=app,
        title='My Documentation',
        version='v1',
        url='/api/docs/swagger.json',
        swagger_path='/api/docs',
    )

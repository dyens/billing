from decimal import Decimal

import pytest
from dynaconf import settings
from sqlalchemy import create_engine

from billing.db.models import (
    Currency,
    metadata,
)
from billing.db.setup import create_pool
from billing.db.transaction import create_transaction
from billing.db.user import create_new_user
from main import init_app


@pytest.fixture(scope='session', autouse=True)
def set_test_settings():
    """Set dynaconf env for testing."""
    settings.configure(ENV_FOR_DYNACONF='testing')


@pytest.fixture()
def pg_database(set_test_settings):
    """Create database and drop it after test."""
    uri = 'postgresql+psycopg2://{username}:{password}@{host}:{port}/{dbname}'.format(
        username=settings.DB['username'],
        password=settings.DB['password'],
        host=settings.DB['host'],
        port=settings.DB['port'],
        dbname=settings.DB['dbname'],
    )
    engine = create_engine(uri)
    metadata.create_all(engine)
    yield
    metadata.drop_all(engine)


@pytest.fixture
async def pg_pool(pg_database, set_test_settings):
    """Pg engine fixture."""
    pool = await create_pool()
    yield pool
    await pool.close()


@pytest.fixture
async def conn(pg_pool):
    """Get connection."""
    async with pg_pool.acquire() as connection:
        yield connection


@pytest.fixture
def cli(loop, aiohttp_client, pg_database):
    """Aiohttp cli fixture."""
    app = init_app()
    return loop.run_until_complete(aiohttp_client(app))


@pytest.fixture
def user_with_wallet_data():
    """User with wallet data."""
    return {
        'name': 'Ivanov',
        'country': 'Russia',
        'city': 'Angarsk',
        'currency': Currency.EUR,
        'balance': Decimal('0.3'),
    }


@pytest.fixture
def user2_with_wallet_data():
    """User2 with wallet data."""
    return {
        'name': 'Petrov',
        'country': 'France',
        'city': 'Paris',
        'currency': Currency.CNY,
        'balance': Decimal('0.4'),
    }


@pytest.fixture
async def user_with_wallet(conn, user_with_wallet_data):
    """Create user1 with wallet fixture."""
    new_user_id = await create_new_user(
        conn,
        **user_with_wallet_data,
    )
    yield new_user_id


@pytest.fixture
async def user2_with_wallet(conn, user2_with_wallet_data):
    """Create user2 with wallet fixture."""
    new_user_id = await create_new_user(
        conn,
        **user2_with_wallet_data,
    )
    yield new_user_id


@pytest.fixture
async def wallet_transaction(
    conn,
    user_with_wallet,
    user2_with_wallet,
):
    """Transaction fixture."""
    new_transaction_id = await create_transaction(
        conn,
        from_wallet_id=user_with_wallet[1],
        to_wallet_id=user2_with_wallet[1],
        amount=Decimal('0.1'),
    )
    yield new_transaction_id

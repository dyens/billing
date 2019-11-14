from decimal import Decimal

import pytest
from dynaconf import settings
from sqlalchemy import create_engine

from billing.db.models import (
    Currency,
    create_new_user,
    metadata,
)
from billing.db.setup import create_pool
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
    return {
        'name': 'Ivanov',
        'country': 'Russia',
        'city': 'Angarsk',
        'currency': Currency.EUR,
        'balance': Decimal('0.3'),
    }


@pytest.fixture
async def user_with_wallet(conn, user_with_wallet_data):
    """Create user with wallet."""
    new_user_id = await create_new_user(
        conn,
        **user_with_wallet_data,
    )
    yield new_user_id

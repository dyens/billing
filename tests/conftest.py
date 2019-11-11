import pytest
from aiohttp import web
from dynaconf import settings
from sqlalchemy import create_engine

from billing.db.models import metadata
from billing.db.setup import (
    close_pg,
    create_pool,
    init_pg,
)
from billing.routes import setup_routes


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
    app = web.Application()
    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)
    setup_routes(app)
    return loop.run_until_complete(aiohttp_client(app))

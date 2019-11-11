"""Setup postgresql connection pool."""

import asyncpgsa
from aiohttp.web_app import Application
from asyncpg.pool import Pool
from dynaconf import settings


async def create_pool() -> Pool:
    """Create connection pool."""
    return await asyncpgsa.create_pool(
        database=settings.DB.dbname,
        user=settings.DB.username,
        password=settings.DB.password,
        host=settings.DB.host,
        port=settings.DB.port,
    )


async def init_pg(app: Application) -> None:
    """Init pg pool for app."""
    pool = await create_pool()
    app['db'] = pool


async def close_pg(app: Application) -> None:
    """Close pg pool for app."""
    await app['db'].close()

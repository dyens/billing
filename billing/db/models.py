"""Models."""

from asyncpg.pool import PoolConnectionProxy
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    select,
)

metadata = MetaData()

user = Table(
    'user',
    metadata,
    Column('id', Integer, primary_key=True),  # NOQA
    Column('name', String, nullable=False),
)


async def get_users(conn: PoolConnectionProxy) -> str:
    """Get all users."""
    query = select([
        user.c.id,
    ]).select_from(user)
    users = await conn.fetch(query)
    return str(users)

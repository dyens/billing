"""Models."""
from dynaconf import settings
import asyncpgsa

from sqlalchemy import (Boolean, Column, DateTime, String, Integer, Text, create_engine, Enum)

from sqlalchemy.ext.declarative import declarative_base


async def init_pg(app):
    engine = await asyncpgsa.create_pool(
        database=settings.DB.dbname,
        user=settings.DB.username,
        password=settings.DB.password,
        host=settings.DB.host,
        port=settings.DB.port,
    )
    app['db'] = engine

async def close_pg(app):
    await app['db'].close()

Base = declarative_base()


class User(Base):
    """User."""

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)  # NOQA
    name = Column(String, nullable=False)


from sqlalchemy import select
async def get_users(conn):
    query = select([User.__table__.c.id, ]).select_from(User.__table__)
    return await conn.fetch(query)


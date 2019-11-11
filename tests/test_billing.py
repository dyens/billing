import pytest

from billing import __version__
from billing.db.models import get_users


def test_version():
    assert __version__ == '0.1.0'




@pytest.mark.asyncio
async def test_users(conn):
    us = await get_users(conn)
    assert us == '[]'


async def test_index(cli):
    response = await cli.get('/')
    text = await response.text()
    assert text == '[]'

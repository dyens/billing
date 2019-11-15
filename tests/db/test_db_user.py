from decimal import Decimal

import pytest

from billing.db.models import (
    user,
    wallet,
)
from billing.db.user import create_new_user


class TestCreateNewUser:
    """Test create new user."""

    @pytest.mark.asyncio
    async def test_success(self, conn, user_with_wallet_data):
        """Testing success create new user."""
        success_data = user_with_wallet_data
        new_user_id, new_wallet_id = await create_new_user(
            conn,
            **success_data,
        )
        assert new_user_id == 1
        assert new_wallet_id == 1

        new_user = await conn.fetchrow(user.select())
        assert new_user['id'] == 1
        assert new_user['name'] == success_data['name']
        assert new_user['country'] == success_data['country']
        assert new_user['city'] == success_data['city']

        new_wallet = await conn.fetchrow(wallet.select())
        assert new_wallet['id'] == 1
        assert new_wallet['user_id'] == 1
        assert new_wallet['balance'] == success_data['balance']
        assert new_wallet['currency'] == success_data['currency'].value

    @pytest.mark.asyncio
    async def test_fail_negative_balance(
        self,
        conn,
        user_with_wallet_data,
    ):
        """Testing failed create new user.

        case: balance < 0
        """
        success_data = user_with_wallet_data
        success_data['balance'] = Decimal('-10')
        with pytest.raises(ValueError):
            await create_new_user(
                conn,
                **success_data,
            )

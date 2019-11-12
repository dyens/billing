from decimal import Decimal

import pytest

from billing.db.models import (
    Currency,
    create_new_user,
    user,
    wallet,
)


class TestCreateNewUser:
    """Test create new user."""

    def success_data(self):
        """Succesed default data."""
        return {
            'name': 'Ivanov',
            'country': 'Russia',
            'city': 'Angarsk',
            'currency': Currency.EUR,
            'balance': Decimal(0.3),  # NOQA:WPS432,
        }

    @pytest.mark.asyncio
    async def test_success(self, conn):
        """Testing success create new user."""
        success_data = self.success_data()
        new_user_id = await create_new_user(
            conn,
            **success_data,
        )
        assert new_user_id == 1

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
    async def test_fail_bad_balance_type(self, conn):
        """Testing failed create new user.

        case: bad balance type
        """
        success_data = self.success_data()
        success_data['balance'] = 'bad value'
        with pytest.raises(ValueError):
            await create_new_user(
                conn,
                **success_data,
            )

    @pytest.mark.asyncio
    async def test_fail_negative_balance(self, conn):
        """Testing failed create new user.

        case: balance < 0
        """
        success_data = self.success_data()
        success_data['balance'] = Decimal('-10')
        with pytest.raises(ValueError):
            await create_new_user(
                conn,
                **success_data,
            )

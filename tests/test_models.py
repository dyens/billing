from decimal import Decimal

import pytest

from billing.db.exceptions import UserDoesNotExists
from billing.db.models import (
    add_to_wallet,
    create_new_user,
    user,
    wallet,
)


class TestCreateNewUser:
    """Test create new user."""

    @pytest.mark.asyncio
    async def test_success(self, conn, user_with_wallet_data):
        """Testing success create new user."""
        success_data = user_with_wallet_data
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
    async def test_fail_bad_balance_type(
        self,
        conn,
        user_with_wallet_data,
    ):
        """Testing failed create new user.

        case: bad balance type
        """
        success_data = user_with_wallet_data
        success_data['balance'] = 'bad value'
        with pytest.raises(ValueError):
            await create_new_user(
                conn,
                **success_data,
            )

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


class TestAddToWallet:
    """Test add to wallet."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        conn,
        user_with_wallet,
        user_with_wallet_data,
    ):
        """Testing success add to wallet."""
        quantity = Decimal(2.5)
        new_balance = await add_to_wallet(
            conn,
            user_id=user_with_wallet,
            quantity=quantity,
        )
        assert new_balance == quantity + user_with_wallet_data['balance']

    @pytest.mark.asyncio
    async def test_fail_wrong_user_id(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: wrong user id
        """
        quantity = Decimal(2.5)

        with pytest.raises(UserDoesNotExists) as exc:
            await add_to_wallet(
                conn,
                user_id=2,
                quantity=quantity,
            )
        assert str(exc.value) == 'User does not exist'

    @pytest.mark.asyncio
    async def test_fail_bad_quantity_type(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: bad quantity type
        """
        quantity = 'Bad type'

        with pytest.raises(ValueError) as exc:
            await add_to_wallet(
                conn,
                user_id=1,
                quantity=quantity,
            )
        assert str(exc.value) == 'Wrong type of quantity'

    @pytest.mark.asyncio
    async def test_fail_neagative_quantity(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: negative quantity
        """
        quantity = Decimal('-3')

        with pytest.raises(ValueError) as exc:
            await add_to_wallet(
                conn,
                user_id=1,
                quantity=quantity,
            )
        assert str(exc.value) == 'Quantity must be positive'

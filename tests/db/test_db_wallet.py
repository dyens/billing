from decimal import Decimal

import pytest

from billing.db.exceptions import WalletDoesNotExists
from billing.db.models import wallet
from billing.db.wallet import (
    add_to_wallet,
    get_from_wallet,
    get_wallet_info,
    is_wallet_exists,
)


class TestIsWalletExists:
    """Test is wallet exists."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        conn,
        user_with_wallet,
    ):
        """Test success case."""
        assert await is_wallet_exists(conn, wallet_id=1) is True

    @pytest.mark.asyncio
    async def test_fail(
        self,
        conn,
        user_with_wallet,
    ):
        """Test fail case."""
        assert await is_wallet_exists(conn, wallet_id=2) is False


class TestGetWalletInfo:
    """Test get wallet infoi."""

    @pytest.mark.asyncio
    async def test_all_data(
        self,
        conn,
        user_with_wallet,
    ):
        """Test all data."""
        wallet_info = await get_wallet_info(conn, wallet_id=1)

        assert wallet_info == {
            'id': 1,
            'user_id': 1,
            'balance': Decimal('0.3'),
            'currency': 'EUR',
        }

    @pytest.mark.asyncio
    async def test_specific_columns(
        self,
        conn,
        user_with_wallet,
    ):
        """Test specific columns."""
        wallet_info = await get_wallet_info(
            conn,
            wallet_id=1,
            columns=[wallet.c.balance, wallet.c.user_id],
        )
        assert wallet_info == {
            'balance': Decimal('0.3'),
            'user_id': 1,
        }


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
        amount = Decimal(2.5)
        new_balance = await add_to_wallet(
            conn,
            wallet_id=user_with_wallet[1],
            amount=amount,
        )
        assert new_balance == amount + user_with_wallet_data['balance']

    @pytest.mark.asyncio
    async def test_fail_wrong_wallet_id(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: wrong user id
        """
        amount = Decimal(2.5)

        with pytest.raises(WalletDoesNotExists) as exc:
            await add_to_wallet(
                conn,
                wallet_id=2,
                amount=amount,
            )
        assert str(exc.value) == 'Wallet does not exists'

    @pytest.mark.asyncio
    async def test_fail_neagative_amount(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: negative amount
        """
        amount = Decimal('-3')

        with pytest.raises(ValueError) as exc:
            await add_to_wallet(
                conn,
                wallet_id=user_with_wallet[1],
                amount=amount,
            )
        assert str(exc.value) == 'Amount must be positive'


class TestGetFromWallet:
    """Test get from wallet."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        conn,
        user_with_wallet,
        user_with_wallet_data,
    ):
        """Testing success add to wallet."""
        amount = Decimal('0.1')
        new_balance = await get_from_wallet(
            conn,
            wallet_id=user_with_wallet[1],
            amount=amount,
        )
        assert new_balance == user_with_wallet_data['balance'] - amount

    @pytest.mark.asyncio
    async def test_fail_wrong_wallet_id(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: wrong user id
        """
        amount = Decimal('0.1')

        with pytest.raises(WalletDoesNotExists) as exc:
            await get_from_wallet(
                conn,
                wallet_id=2,
                amount=amount,
            )
        assert str(exc.value) == 'Wallet does not exists'

    @pytest.mark.asyncio
    async def test_fail_neagative_amount(self, conn, user_with_wallet):
        """Testing failed add to wallet.

        case: negative amount
        """
        amount = Decimal('-3')

        with pytest.raises(ValueError) as exc:
            await get_from_wallet(
                conn,
                wallet_id=user_with_wallet[1],
                amount=amount,
            )
        assert str(exc.value) == 'Amount must be positive'

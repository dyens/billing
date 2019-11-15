from decimal import Decimal

import pytest

from billing.db.exceptions import WalletDoesNotExists
from billing.db.models import (
    FailedReason,
    TransactionState,
    add_to_wallet,
    add_transaction_log,
    create_new_user,
    create_transaction,
    fail_transaction,
    get_from_wallet,
    get_wallet_info,
    is_wallet_exists,
    success_transaction,
    transaction,
    transaction_log,
    transfer_between_wallets,
    user,
    validate_transaction,
    wallet,
)


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
        info = await get_wallet_info(conn, wallet_id=1)

        assert info == {
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

        info = await get_wallet_info(
            conn,
            wallet_id=1,
            columns=[wallet.c.balance, wallet.c.user_id],
        )
        assert info == {
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


class TestAddTransactionLog:
    """Test add transaction log."""

    @pytest.mark.asyncio
    async def test_add_transaction_log(
        self,
        conn,
        wallet_transaction,
    ):
        """Test add transaction log."""
        await add_transaction_log(
            conn,
            transaction_id=wallet_transaction,
            state=TransactionState.FAILED,
            comment='Test comment',
        )
        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 2
        log = logs[1]
        assert log['transaction_id'] == 1
        assert log['state'] == 'FAILED'
        assert log['comment'] == 'Test comment'


class TestCreateTransaction:
    """Test create transaction."""

    @pytest.mark.asyncio
    async def test_create_transaction(
        self,
        conn,
        wallet_transaction,
    ):
        """Test create transaction."""

        transaction_info = await conn.fetchrow(transaction.select())
        assert transaction_info['from_wallet_id'] == 1
        assert transaction_info['to_wallet_id'] == 2
        assert transaction_info['state'] == 'CREATED'
        assert transaction_info['amount'] == Decimal('0.1')
        assert transaction_info['exchange_from_rate'] is None
        assert transaction_info['exchange_to_rate'] is None
        assert transaction_info['failed_reason'] is None
        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 1
        log = logs[0]
        assert log['transaction_id'] == 1
        assert log['state'] == 'CREATED'
        assert log['comment'] == 'Transaction created'


class TestFailTransaction:
    """Test fail transaction."""

    @pytest.mark.asyncio
    async def test_fail_transaction(
        self,
        conn,
        wallet_transaction,
    ):
        """Test fail transaction."""
        await fail_transaction(
            conn,
            transaction_id=wallet_transaction,
            reason=FailedReason.NEM_FROM_WALLET,
            comment='Failed reason',
        )

        transaction_info = await conn.fetchrow(transaction.select())
        assert transaction_info['from_wallet_id'] == 1
        assert transaction_info['to_wallet_id'] == 2
        assert transaction_info['state'] == 'FAILED'
        assert transaction_info['amount'] == Decimal('0.1')
        assert transaction_info['exchange_from_rate'] is None
        assert transaction_info['exchange_to_rate'] is None
        assert transaction_info['failed_reason'] == 'NEM_FROM_WALLET'
        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 2
        log = logs[1]
        assert log['transaction_id'] == 1
        assert log['state'] == 'FAILED'
        assert log['comment'] == 'Failed reason'


class TestSuccessTransaction:
    """Test success transaction."""

    @pytest.mark.asyncio
    async def test_success_transaction(
        self,
        conn,
        wallet_transaction,
    ):
        """Test success transaction."""
        await success_transaction(
            conn,
            transaction_id=wallet_transaction,
            exchange_from_rate=Decimal('0.1'),
            exchange_to_rate=Decimal('0.2'),
            comment='Success reason',
        )

        transaction_info = await conn.fetchrow(transaction.select())
        assert transaction_info['from_wallet_id'] == 1
        assert transaction_info['to_wallet_id'] == 2
        assert transaction_info['state'] == 'SUCCESED'
        assert transaction_info['amount'] == Decimal('0.1')
        assert transaction_info['exchange_from_rate'] == Decimal('0.1')
        assert transaction_info['exchange_to_rate'] == Decimal('0.2')
        assert transaction_info['failed_reason'] is None
        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 2
        log = logs[1]
        assert log['transaction_id'] == 1
        assert log['state'] == 'SUCCESED'
        assert log['comment'] == 'Success reason'


class TestValidateTransaction:
    """Test validate transaction."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        conn,
        wallet_transaction,
    ):
        """Test success validate transaction."""
        is_valid = await validate_transaction(
            conn,
            transaction_id=wallet_transaction,
        )
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_failed(
        self,
        conn,
        wallet_transaction,
    ):
        """Test fail validate transaction.
        
        Case: not enough moeny.
        """
        await conn.execute(
            transaction.update().where(transaction.c.id == wallet_transaction
                                       ).values(amount=Decimal('1000'))
        )
        is_valid = await validate_transaction(
            conn,
            transaction_id=wallet_transaction,
        )
        assert is_valid is False

        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 2
        log = logs[1]
        assert log['transaction_id'] == 1
        assert log['state'] == 'FAILED'
        assert log['comment'] == 'Not enough balance'


class TestTransferBetweenWallets:
    """Test transfer between wallets."""

    @pytest.mark.asyncio
    async def test_success(
        self,
        conn,
        user_with_wallet,
        user2_with_wallet,
    ):

        wallet_from_info = await get_wallet_info(conn, wallet_id=user_with_wallet[1])
        assert wallet_from_info['balance'] == Decimal('0.3')

        wallet_to_info = await get_wallet_info(conn, wallet_id=user2_with_wallet[1])
        assert wallet_to_info['balance'] == Decimal('0.4')


        await transfer_between_wallets(
            conn,
            from_wallet_id=user_with_wallet[1],
            to_wallet_id=user2_with_wallet[1],
            amount=Decimal('0.1'),
        )

        # 0.3 - 0.1 = 0.2
        wallet_from_info = await get_wallet_info(conn, wallet_id=user_with_wallet[1])
        assert wallet_from_info['balance'] == Decimal('0.2')

        # 0.4 + 0.1 * 1.15 [EUR -> USD] / 0.14 [USD -> CNY]
        wallet_to_info = await get_wallet_info(conn, wallet_id=user2_with_wallet[1])
        assert round(wallet_to_info['balance'], 3) == Decimal('1.186')

        transaction_info = await conn.fetchrow(transaction.select())
        assert transaction_info['from_wallet_id'] == 1
        assert transaction_info['to_wallet_id'] == 2
        assert transaction_info['state'] == 'SUCCESED'
        assert transaction_info['amount'] == Decimal('0.1')
        assert round(transaction_info['exchange_from_rate'], 3) == Decimal('1.153')
        assert round(transaction_info['exchange_to_rate'], 3) == Decimal('0.147')
        assert transaction_info['failed_reason'] is None
        logs = list(await conn.fetch(transaction_log.select()))
        # First log is creation log
        assert len(logs) == 2
        log = logs[1]
        assert log['transaction_id'] == 1
        assert log['state'] == 'SUCCESED'
        assert log['comment'] == 'Success'


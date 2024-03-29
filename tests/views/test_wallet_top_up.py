from decimal import Decimal

from billing.db.models import wallet


class TestWalletTopUp:
    """Test wallet top up."""

    url = '/v1/wallet_top_up'

    async def test_success(self, cli, user_with_wallet):
        """Test succes wallet top up."""
        request_data = {'wallet_id': 1, 'amount': '0.21'}
        response = await cli.post(
            self.url,
            data=request_data,
        )
        response_json = await response.json()
        assert response_json['new_balance'] == '0.51'

        async with cli.app['db'].acquire() as connection:
            new_wallet = await connection.fetchrow(wallet.select())
            assert new_wallet['balance'] == Decimal('0.51')

    async def test_many_success(self, cli, user_with_wallet):
        """Test succes wallet top up."""
        request_data = {'wallet_id': 1, 'amount': '0.21'}
        await cli.post(
            self.url,
            data=request_data,
        )
        response = await cli.post(
            self.url,
            data=request_data,
        )
        response_json = await response.json()
        assert response_json['new_balance'] == '0.72'

        async with cli.app['db'].acquire() as connection:
            new_wallet = await connection.fetchrow(wallet.select())
            assert new_wallet['balance'] == Decimal('0.72')

    async def test_fail_bad_wallet_id(self, cli):
        """Testing failed wallet top up.

        case: bad wallet id
        """
        request_data = {'wallet_id': 2, 'amount': '0.21'}
        response = await cli.post(
            self.url,
            data=request_data,
        )

        assert response.status == 404
        response_text = await response.text()
        assert response_text == '404: Wallet does not exists'

    async def test_fail_bad_amount_type(self, cli):
        """Testing failed wallet top up.

        case: bad amount type
        """
        request_data = {'wallet_id': 1, 'amount': 'bad qunatity'}
        response = await cli.post(
            self.url,
            data=request_data,
        )

        assert response.status == 422
        response_json = await response.json()
        assert response_json['amount'] == ['Not a valid number.']

    async def test_fail_negative_amount(self, cli):
        """Testing failed wallet top up.

        case: negative amount
        """
        request_data = {'wallet_id': 1, 'amount': '-0.1'}
        response = await cli.post(
            self.url,
            data=request_data,
        )

        assert response.status == 422
        response_json = await response.json()
        assert response_json['amount'] == ['Negative amount.']

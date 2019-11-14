from decimal import Decimal

from billing.db.models import (
    Currency,
    user,
    wallet,
)


class TestUserRegister:
    """Test user registration."""

    url = '/v1/user_register'

    def default_data(self):
        """Succesed default data."""
        return {
            'name': 'Ivanov',
            'country': 'Russia',
            'city': 'Angarsk',
            'currency': Currency.EUR.value,
            'balance': '0.3',
        }

    async def test_success(self, cli):
        """Test succes user registration."""
        request_data = self.default_data()
        response = await cli.post(
            self.url,
            data=request_data,
        )
        response_json = await response.json()
        assert response_json['new_user_id'] == 1
        assert response_json['new_wallet_id'] == 1

        async with cli.app['db'].acquire() as connection:
            new_user = await connection.fetchrow(user.select())
            assert new_user['id'] == 1
            assert new_user['name'] == request_data['name']
            assert new_user['country'] == request_data['country']
            assert new_user['city'] == request_data['city']

            new_wallet = await connection.fetchrow(wallet.select())
            assert new_wallet['id'] == 1
            assert new_wallet['user_id'] == 1
            assert new_wallet['balance'] == Decimal(request_data['balance'])
            assert new_wallet['currency'] == request_data['currency']

    async def test_many_success(self, cli):
        """Test succes many user registrations."""
        request_data = self.default_data()
        response = await cli.post(
            self.url,
            data=request_data,
        )
        response_json = await response.json()
        assert response_json['new_user_id'] == 1
        assert response_json['new_wallet_id'] == 1

        response = await cli.post(
            self.url,
            data=request_data,
        )
        response_json = await response.json()
        assert response_json['new_user_id'] == 2
        assert response_json['new_wallet_id'] == 2

    async def test_fail_bad_balance_type(self, cli):
        """Testing failed register user.

        case: bad balance type
        """
        request_data = self.default_data()
        request_data['balance'] = 'asdf'
        response = await cli.post(
            self.url,
            data=request_data,
        )
        assert response.status == 422
        response_json = await response.json()
        assert response_json == {'balance': ['Not a valid number.']}

    async def test_fail_negative_balance(self, cli):
        """Testing failed register user.

        case: negative balance
        """
        request_data = self.default_data()
        request_data['balance'] = '-1'
        response = await cli.post(
            self.url,
            data=request_data,
        )
        assert response.status == 422
        response_json = await response.json()
        assert response_json == {'balance': ['Negative balance.']}

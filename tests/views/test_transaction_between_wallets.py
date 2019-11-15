import billing.views.transaction_between_wallets  # NOQA: WPS301


async def transfer_between_wallets_job_mock(
    from_wallet_id,
    to_wallet_id,
    amount,
):
    """Transfer job mock function."""
    return None  # NOQA: WPS324


class TestTransactionBetweenWallets:
    """Test transaction between wallets."""

    url = '/v1/transaction_between_wallets'

    async def test_success(
        self,
        cli,
        user_with_wallet,
        user2_with_wallet,
        monkeypatch,
    ):
        """Test succes transaction."""
        monkeypatch.setattr(
            billing.views.transaction_between_wallets,
            'transfer_between_wallets_job',
            transfer_between_wallets_job_mock,
        )
        response = await cli.post(
            self.url,
            data={
                'from_wallet_id': 1,
                'to_wallet_id': 2,
                'amount': '0.01',
            },
        )
        response_json = await response.json()
        assert response_json['msg'] == 'Transaction created'

    async def test_fail_bad_amount_type(
        self,
        cli,
        user_with_wallet,
        user2_with_wallet,
    ):
        """Test fail.

        Case: bad amount.
        """
        response = await cli.post(
            self.url,
            data={
                'from_wallet_id': 1,
                'to_wallet_id': 2,
                'amount': 'bad amount',
            },
        )
        assert response.status == 422
        response_json = await response.json()
        assert response_json['amount'] == ['Not a valid number.']

    async def test_fail_negative_amount(
        self,
        cli,
        user_with_wallet,
        user2_with_wallet,
    ):
        """Test fail.

        Case: negative amount.
        """
        response = await cli.post(
            self.url,
            data={
                'from_wallet_id': 1,
                'to_wallet_id': 2,
                'amount': '-10',
            },
        )
        assert response.status == 422
        response_json = await response.json()
        assert response_json['amount'] == ['Negative amount.']

    async def test_fail_transfer_yourself(
        self,
        cli,
    ):
        """Test fail.

        Case: transfer yourself.
        """
        response = await cli.post(
            self.url,
            data={
                'from_wallet_id': 1,
                'to_wallet_id': 1,
                'amount': '10',
            },
        )
        assert response.status == 422
        response_text = await response.text()
        assert response_text == '422: Transfer yourself'

    async def test_fail_bad_wallet(
        self,
        cli,
        user_with_wallet,
        user2_with_wallet,
    ):
        """Test fail.

        Case: negative amount.
        """
        response = await cli.post(
            self.url,
            data={
                'from_wallet_id': 3,
                'to_wallet_id': 2,
                'amount': '10',
            },
        )
        assert response.status == 404
        response_text = await response.text()
        assert response_text == '404: Wallet 3 does not exist'

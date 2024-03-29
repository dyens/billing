"""init migration

Revision ID: 1bf08bb6a672
Revises: 
Create Date: 2019-11-15 16:08:55.298560

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1bf08bb6a672'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('country', sa.String(), nullable=False),
    sa.Column('city', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('wallet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('balance', sa.Numeric(), nullable=False),
    sa.Column('currency', sa.Enum('USD', 'EUR', 'CAD', 'CNY', name='currency'), nullable=False),
    sa.CheckConstraint('balance >= 0', name='positive_balance'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transaction',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('from_wallet_id', sa.Integer(), nullable=False),
    sa.Column('to_wallet_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.Enum('CREATED', 'SUCCESED', 'FAILED', name='transactionstate'), nullable=False),
    sa.Column('amount', sa.Numeric(), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('new_balance_from', sa.Numeric(), nullable=True),
    sa.Column('new_balance_to', sa.Numeric(), nullable=True),
    sa.Column('exchange_from_rate', sa.Numeric(), nullable=True),
    sa.Column('exchange_to_rate', sa.Numeric(), nullable=True),
    sa.Column('failed_reason', sa.Enum('NEM_FROM_WALLET', 'CUR_API_NA', 'UNKNOWN', name='failedreason'), nullable=True),
    sa.ForeignKeyConstraint(['from_wallet_id'], ['wallet.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_wallet_id'], ['wallet.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('transaction_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('transaction_id', sa.Integer(), nullable=False),
    sa.Column('state', sa.Enum('CREATED', 'SUCCESED', 'FAILED', name='transactionstate'), nullable=False),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['transaction_id'], ['transaction.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('transaction_log')
    op.drop_table('transaction')
    op.drop_table('wallet')
    op.drop_table('user')
    # ### end Alembic commands ###

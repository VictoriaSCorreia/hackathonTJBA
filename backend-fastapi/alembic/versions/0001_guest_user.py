"""initial guest user model

Revision ID: 0001_guest_user
Revises: 
Create Date: 2025-10-11

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001_guest_user'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('guest_id', sa.String(), nullable=False),
        sa.UniqueConstraint('guest_id', name='uq_users_guest_id'),
    )
    op.create_index('ix_users_guest_id', 'users', ['guest_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_users_guest_id', table_name='users')
    op.drop_table('users')


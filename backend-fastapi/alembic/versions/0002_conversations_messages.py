"""conversations and messages tables

Revision ID: 0002_conversations_messages
Revises: 0001_guest_user
Create Date: 2025-10-11

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_conversations_messages'
down_revision = '0001_guest_user'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'conversations' not in existing_tables:
        op.create_table(
            'conversations',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('guest_id', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=False), nullable=False),
        )
    # Índice pode já existir se a migração foi tentada previamente; usar SQL idempotente
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_conversations_guest_id ON conversations (guest_id)"))

    if 'messages' not in existing_tables:
        op.create_table(
            'messages',
            sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
            sa.Column('conversation_id', sa.Integer(), sa.ForeignKey('conversations.id'), nullable=False),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=False), nullable=False),
        )
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id)"))


def downgrade() -> None:
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')
    op.drop_index('ix_conversations_guest_id', table_name='conversations')
    op.drop_table('conversations')

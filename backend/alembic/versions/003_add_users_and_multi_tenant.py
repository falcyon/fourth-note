"""Add users table and multi-tenant foreign keys

Revision ID: 003
Revises: 002
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('google_id', sa.String(255), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(500)),
        sa.Column('picture_url', sa.String(1000)),
        sa.Column('gmail_token_json', JSONB),
        sa.Column('is_demo_account', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Add user_id foreign key to emails table
    op.add_column('emails', sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')))
    op.create_index('ix_emails_user_id', 'emails', ['user_id'])

    # Add user_id foreign key to documents table
    op.add_column('documents', sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')))
    op.create_index('ix_documents_user_id', 'documents', ['user_id'])

    # Add user_id foreign key to investments table
    op.add_column('investments', sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id')))
    op.create_index('ix_investments_user_id', 'investments', ['user_id'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('ix_investments_user_id', table_name='investments')
    op.drop_index('ix_documents_user_id', table_name='documents')
    op.drop_index('ix_emails_user_id', table_name='emails')

    # Remove user_id columns
    op.drop_column('investments', 'user_id')
    op.drop_column('documents', 'user_id')
    op.drop_column('emails', 'user_id')

    # Drop users table
    op.drop_table('users')

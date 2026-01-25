"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('gmail_message_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('subject', sa.String(500)),
        sa.Column('sender', sa.String(255)),
        sa.Column('received_at', sa.DateTime()),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('emails.id'), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000)),
        sa.Column('markdown_content', sa.Text()),
        sa.Column('processing_status', sa.String(50), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create investments table
    op.create_table(
        'investments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id'), nullable=False),
        sa.Column('investment_name', sa.String(500)),
        sa.Column('firm', sa.String(500)),
        sa.Column('strategy_description', sa.Text()),
        sa.Column('leaders', sa.Text()),
        sa.Column('management_fees', sa.String(255)),
        sa.Column('incentive_fees', sa.String(255)),
        sa.Column('liquidity_lock', sa.String(255)),
        sa.Column('target_net_returns', sa.String(255)),
        sa.Column('raw_extraction_json', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('ix_documents_email_id', 'documents', ['email_id'])
    op.create_index('ix_investments_document_id', 'investments', ['document_id'])
    op.create_index('ix_investments_created_at', 'investments', ['created_at'])


def downgrade() -> None:
    op.drop_index('ix_investments_created_at')
    op.drop_index('ix_investments_document_id')
    op.drop_index('ix_documents_email_id')
    op.drop_table('investments')
    op.drop_table('documents')
    op.drop_table('emails')

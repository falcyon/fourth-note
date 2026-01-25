"""Investment-centric schema with field-level attribution

Revision ID: 004
Revises: 003
Create Date: 2026-01-25

This migration:
1. Removes document_id FK from investments (documents now linked via junction table)
2. Adds notes and is_archived columns to investments
3. Creates investment_documents junction table
4. Creates field_values table for field-level source attribution
5. Makes email_id nullable on documents (for future manual uploads)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Modify investments table
    # Remove document_id FK and add new columns
    op.drop_constraint('investments_document_id_fkey', 'investments', type_='foreignkey')
    op.drop_column('investments', 'document_id')
    op.drop_column('investments', 'raw_extraction_json')

    # Add new columns
    op.add_column('investments', sa.Column('notes', sa.Text))
    op.add_column('investments', sa.Column('is_archived', sa.Boolean, server_default='false'))

    # 2. Make email_id nullable on documents (for future manual uploads)
    op.alter_column('documents', 'email_id', nullable=True)

    # 3. Create investment_documents junction table
    op.create_table(
        'investment_documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('investment_id', UUID(as_uuid=True), sa.ForeignKey('investments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relationship', sa.String(50), server_default='source'),  # 'source', 'reference', 'supplement'
        sa.Column('added_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_investment_documents_investment_id', 'investment_documents', ['investment_id'])
    op.create_index('ix_investment_documents_document_id', 'investment_documents', ['document_id'])
    op.create_unique_constraint('uq_investment_documents', 'investment_documents', ['investment_id', 'document_id'])

    # 4. Create field_values table
    op.create_table(
        'field_values',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('investment_id', UUID(as_uuid=True), sa.ForeignKey('investments.id', ondelete='CASCADE'), nullable=False),

        # What field this is
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('field_value', sa.Text),

        # Source attribution
        sa.Column('source_type', sa.String(50), nullable=False),  # 'document', 'manual', 'web', 'api'
        sa.Column('source_id', UUID(as_uuid=True)),  # References document_id, etc.
        sa.Column('source_name', sa.String(500)),  # Display name

        # Location within source (for future "hover to see context" feature)
        sa.Column('source_location_start', sa.Integer),  # Markdown line/char offset
        sa.Column('source_location_end', sa.Integer),
        sa.Column('source_context', sa.Text),  # Text snippet from source

        # For time-series data (quarterly revenue, leadership changes, etc.)
        sa.Column('effective_date', sa.Date),  # When this value was true
        sa.Column('period_type', sa.String(20)),  # 'quarterly', 'annual', 'point_in_time', null

        # Status
        sa.Column('is_current', sa.Boolean, server_default='true'),  # Is this the active value?
        sa.Column('confidence', sa.String(20), server_default='medium'),  # 'low', 'medium', 'high', 'verified'

        # Timestamps
        sa.Column('extracted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Indexes for field_values
    op.create_index('ix_field_values_investment_id', 'field_values', ['investment_id'])
    op.create_index('ix_field_values_investment_field', 'field_values', ['investment_id', 'field_name'])
    op.create_index('ix_field_values_source_id', 'field_values', ['source_id'])
    # Partial index for current values (PostgreSQL specific)
    op.execute('''
        CREATE INDEX ix_field_values_current
        ON field_values (investment_id, field_name)
        WHERE is_current = true
    ''')
    # Partial index for time-series data
    op.execute('''
        CREATE INDEX ix_field_values_timeseries
        ON field_values (investment_id, field_name, effective_date)
        WHERE effective_date IS NOT NULL
    ''')


def downgrade() -> None:
    # Drop partial indexes
    op.execute('DROP INDEX IF EXISTS ix_field_values_timeseries')
    op.execute('DROP INDEX IF EXISTS ix_field_values_current')

    # Drop regular indexes
    op.drop_index('ix_field_values_source_id', table_name='field_values')
    op.drop_index('ix_field_values_investment_field', table_name='field_values')
    op.drop_index('ix_field_values_investment_id', table_name='field_values')

    # Drop field_values table
    op.drop_table('field_values')

    # Drop investment_documents table
    op.drop_constraint('uq_investment_documents', 'investment_documents', type_='unique')
    op.drop_index('ix_investment_documents_document_id', table_name='investment_documents')
    op.drop_index('ix_investment_documents_investment_id', table_name='investment_documents')
    op.drop_table('investment_documents')

    # Restore email_id not nullable on documents
    op.alter_column('documents', 'email_id', nullable=False)

    # Remove new columns from investments
    op.drop_column('investments', 'is_archived')
    op.drop_column('investments', 'notes')

    # Restore document_id column on investments
    op.add_column('investments', sa.Column('raw_extraction_json', sa.JSON))
    op.add_column('investments', sa.Column('document_id', UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('investments_document_id_fkey', 'investments', 'documents', ['document_id'], ['id'])

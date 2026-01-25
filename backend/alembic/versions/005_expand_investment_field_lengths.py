"""Expand investment field lengths from VARCHAR(255) to TEXT

Revision ID: 005
Revises: 004
Create Date: 2026-01-25

AI extraction can produce lengthy content for fields like liquidity_lock,
management_fees, etc. This migration changes them from VARCHAR(255) to TEXT.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change VARCHAR(255) columns to TEXT for investments table
    op.alter_column('investments', 'management_fees',
                    existing_type=sa.VARCHAR(255),
                    type_=sa.Text(),
                    existing_nullable=True)

    op.alter_column('investments', 'incentive_fees',
                    existing_type=sa.VARCHAR(255),
                    type_=sa.Text(),
                    existing_nullable=True)

    op.alter_column('investments', 'liquidity_lock',
                    existing_type=sa.VARCHAR(255),
                    type_=sa.Text(),
                    existing_nullable=True)

    op.alter_column('investments', 'target_net_returns',
                    existing_type=sa.VARCHAR(255),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert to VARCHAR(255) - may truncate data!
    op.alter_column('investments', 'management_fees',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(255),
                    existing_nullable=True)

    op.alter_column('investments', 'incentive_fees',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(255),
                    existing_nullable=True)

    op.alter_column('investments', 'liquidity_lock',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(255),
                    existing_nullable=True)

    op.alter_column('investments', 'target_net_returns',
                    existing_type=sa.Text(),
                    type_=sa.VARCHAR(255),
                    existing_nullable=True)

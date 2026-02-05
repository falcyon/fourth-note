"""Add body_text column to emails table

Revision ID: 007
Revises: 006
Create Date: 2026-02-05

Stores the plain text body of emails for use in triage classification.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('emails', sa.Column('body_text', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('emails', 'body_text')

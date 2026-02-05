"""Convert leaders field to JSON format with LinkedIn URLs

Revision ID: 006
Revises: 005
Create Date: 2026-02-02

Converts the pipe-separated leaders text field to a JSONB array with
structured leader objects containing name and linkedin_url.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new leaders_json column
    op.add_column('investments', sa.Column('leaders_json', JSONB, nullable=True))

    # Migrate existing data from leaders (pipe-separated) to leaders_json (JSON array)
    # This is done via raw SQL for efficiency
    op.execute("""
        UPDATE investments
        SET leaders_json = (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'name', trim(leader),
                    'linkedin_url', NULL
                )
            )
            FROM unnest(string_to_array(leaders, '|')) AS leader
            WHERE trim(leader) != ''
        )
        WHERE leaders IS NOT NULL AND leaders != ''
    """)

    # Drop the old leaders column
    op.drop_column('investments', 'leaders')


def downgrade() -> None:
    # Add back the leaders column
    op.add_column('investments', sa.Column('leaders', sa.Text(), nullable=True))

    # Convert JSON back to pipe-separated string
    op.execute("""
        UPDATE investments
        SET leaders = (
            SELECT string_agg(leader->>'name', ' | ')
            FROM jsonb_array_elements(leaders_json) AS leader
        )
        WHERE leaders_json IS NOT NULL
    """)

    # Drop the leaders_json column
    op.drop_column('investments', 'leaders_json')

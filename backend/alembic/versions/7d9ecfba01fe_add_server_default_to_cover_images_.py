"""Add server default to cover_images.created_at

Revision ID: 7d9ecfba01fe
Revises: 1ac2aee111f0
Create Date: 2025-12-26 13:09:43.397114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d9ecfba01fe'
down_revision: Union[str, Sequence[str], None] = '1ac2aee111f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "cover_images",
        "created_at",
        server_default=sa.text("now()"),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )

def downgrade() -> None:
    op.alter_column(
        "cover_images",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
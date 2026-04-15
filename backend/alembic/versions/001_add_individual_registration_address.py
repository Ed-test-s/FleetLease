"""add registration_address to individuals

Revision ID: 001_reg_addr
Revises:
Create Date: 2026-04-14

"""

from alembic import op
from sqlalchemy import text

revision = "001_reg_addr"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text(
            "ALTER TABLE individuals ADD COLUMN IF NOT EXISTS registration_address TEXT"
        )
    )


def downgrade() -> None:
    op.execute(text("ALTER TABLE individuals DROP COLUMN IF EXISTS registration_address"))

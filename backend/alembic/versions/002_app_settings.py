"""app_settings singleton for VAT rate

Revision ID: 002_app_settings
Revises: 001_reg_addr
Create Date: 2026-04-16

"""

from alembic import op
import sqlalchemy as sa

revision = "002_app_settings"
down_revision = "001_reg_addr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vat_rate_percent", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("app_settings")

"""Add quantity to lease requests

Revision ID: 010_requests_quantity
Revises: 009_interest_vat_amount
Create Date: 2026-05-12

"""

from alembic import op
import sqlalchemy as sa

revision = "010_requests_quantity"
down_revision = "009_interest_vat_amount"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "requests",
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("requests", "quantity", server_default=None)


def downgrade() -> None:
    op.drop_column("requests", "quantity")

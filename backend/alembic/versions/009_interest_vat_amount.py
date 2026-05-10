"""Add interest VAT amount to payment schedule

Revision ID: 009_interest_vat_amount
Revises: 008_notification_type_and_entity
Create Date: 2026-05-10

"""

from alembic import op
import sqlalchemy as sa

revision = "009_interest_vat_amount"
down_revision = "008_notification_type_and_entity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "payment_schedule",
        sa.Column("interest_vat_amount", sa.Float(), nullable=False, server_default="0"),
    )
    op.alter_column("payment_schedule", "interest_vat_amount", server_default=None)


def downgrade() -> None:
    op.drop_column("payment_schedule", "interest_vat_amount")

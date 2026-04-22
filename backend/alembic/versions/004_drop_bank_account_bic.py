"""Drop bank_accounts.bic; copy to swift; swift NOT NULL

Revision ID: 004_drop_bank_bic
Revises: 003_supplier_req
Create Date: 2026-04-22

"""

from alembic import op
import sqlalchemy as sa

revision = "004_drop_bank_bic"
down_revision = "003_supplier_req"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE bank_accounts
        SET swift = bic
        WHERE (swift IS NULL OR btrim(swift) = '')
          AND bic IS NOT NULL
          AND btrim(bic) <> ''
        """
    )
    op.drop_column("bank_accounts", "bic")
    op.alter_column(
        "bank_accounts",
        "swift",
        existing_type=sa.String(length=11),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "bank_accounts",
        "swift",
        existing_type=sa.String(length=11),
        nullable=True,
    )
    op.add_column("bank_accounts", sa.Column("bic", sa.String(length=11), nullable=True))

"""Add bank account references to contracts

Revision ID: 006_contract_bank_accounts
Revises: 005_about_page_json
Create Date: 2026-05-09

"""

from alembic import op
import sqlalchemy as sa

revision = "006_contract_bank_accounts"
down_revision = "005_about_page_json"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contracts", sa.Column("lessor_bank_account_id", sa.Integer(), nullable=True))
    op.add_column("contracts", sa.Column("lessee_bank_account_id", sa.Integer(), nullable=True))
    op.add_column("contracts", sa.Column("supplier_bank_account_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_contracts_lessor_bank_account",
        "contracts", "bank_accounts",
        ["lessor_bank_account_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_contracts_lessee_bank_account",
        "contracts", "bank_accounts",
        ["lessee_bank_account_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_contracts_supplier_bank_account",
        "contracts", "bank_accounts",
        ["supplier_bank_account_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_contracts_supplier_bank_account", "contracts", type_="foreignkey")
    op.drop_constraint("fk_contracts_lessee_bank_account", "contracts", type_="foreignkey")
    op.drop_constraint("fk_contracts_lessor_bank_account", "contracts", type_="foreignkey")
    op.drop_column("contracts", "supplier_bank_account_id")
    op.drop_column("contracts", "lessee_bank_account_id")
    op.drop_column("contracts", "lessor_bank_account_id")

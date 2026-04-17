"""Add supplier_requests table and extend contracts/chats

Revision ID: 003_supplier_req
Revises: 002_app_settings
Create Date: 2026-04-17

"""

from alembic import op
import sqlalchemy as sa

revision = "003_supplier_req"
down_revision = "002_app_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("lease_request_id", sa.Integer(), nullable=False),
        sa.Column("lessor_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum("new", "in_review", "approved", "rejected", name="supplierrequeststatus"),
            nullable=False,
            server_default="new",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["lease_request_id"], ["requests.id"]),
        sa.ForeignKeyConstraint(["lessor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"]),
    )

    op.add_column("contracts", sa.Column("supplier_request_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_contracts_supplier_request_id",
        "contracts",
        "supplier_requests",
        ["supplier_request_id"],
        ["id"],
    )

    op.add_column(
        "contracts",
        sa.Column(
            "contract_type",
            sa.Enum("lease", "purchase_sale", name="contracttype"),
            nullable=False,
            server_default="lease",
        ),
    )
    op.add_column("contracts", sa.Column("signing_date", sa.Date(), nullable=True))
    op.add_column("contracts", sa.Column("signing_city", sa.String(200), nullable=True))
    op.add_column("contracts", sa.Column("currency", sa.String(10), nullable=True))
    op.add_column("contracts", sa.Column("vat_rate", sa.Float(), nullable=True))
    op.add_column("contracts", sa.Column("tech_passport_number", sa.String(100), nullable=True))
    op.add_column("contracts", sa.Column("tech_passport_date", sa.Date(), nullable=True))
    op.add_column("contracts", sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"))

    op.add_column("contracts", sa.Column("lessee_confirmed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("contracts", sa.Column("lessor_confirmed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("contracts", sa.Column("supplier_confirmed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("contracts", sa.Column("all_confirmed", sa.Boolean(), nullable=False, server_default="false"))

    op.add_column("contracts", sa.Column("psa_doc_url", sa.String(500), nullable=True))
    op.add_column("contracts", sa.Column("la_doc_url", sa.String(500), nullable=True))

    op.alter_column("contracts", "request_id", existing_type=sa.Integer(), nullable=True)
    op.alter_column("contracts", "lessee_id", existing_type=sa.Integer(), nullable=True)

    op.add_column("chats", sa.Column("supplier_request_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_chats_supplier_request_id",
        "chats",
        "supplier_requests",
        ["supplier_request_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_chats_supplier_request_id", "chats", type_="foreignkey")
    op.drop_column("chats", "supplier_request_id")

    op.alter_column("contracts", "lessee_id", existing_type=sa.Integer(), nullable=False)
    op.alter_column("contracts", "request_id", existing_type=sa.Integer(), nullable=False)

    op.drop_column("contracts", "la_doc_url")
    op.drop_column("contracts", "psa_doc_url")
    op.drop_column("contracts", "all_confirmed")
    op.drop_column("contracts", "supplier_confirmed")
    op.drop_column("contracts", "lessor_confirmed")
    op.drop_column("contracts", "lessee_confirmed")
    op.drop_column("contracts", "quantity")
    op.drop_column("contracts", "tech_passport_date")
    op.drop_column("contracts", "tech_passport_number")
    op.drop_column("contracts", "vat_rate")
    op.drop_column("contracts", "currency")
    op.drop_column("contracts", "signing_city")
    op.drop_column("contracts", "signing_date")
    op.drop_column("contracts", "contract_type")

    op.drop_constraint("fk_contracts_supplier_request_id", "contracts", type_="foreignkey")
    op.drop_column("contracts", "supplier_request_id")

    op.drop_table("supplier_requests")
    sa.Enum("new", "in_review", "approved", "rejected", name="supplierrequeststatus").drop(op.get_bind())
    sa.Enum("lease", "purchase_sale", name="contracttype").drop(op.get_bind())

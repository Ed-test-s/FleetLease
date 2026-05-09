"""Create favorites table

Revision ID: 007_favorites
Revises: 006_contract_bank_accounts
Create Date: 2026-05-09

"""

from alembic import op
import sqlalchemy as sa

revision = "007_favorites"
down_revision = "006_contract_bank_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("favorites"):
        op.create_table(
            "favorites",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("vehicle_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "vehicle_id", name="uq_favorite_user_vehicle"),
        )
        op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
        op.create_index("ix_favorites_vehicle_id", "favorites", ["vehicle_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("favorites"):
        index_names = {idx["name"] for idx in inspector.get_indexes("favorites")}
        if "ix_favorites_vehicle_id" in index_names:
            op.drop_index("ix_favorites_vehicle_id", table_name="favorites")
        if "ix_favorites_user_id" in index_names:
            op.drop_index("ix_favorites_user_id", table_name="favorites")
        op.drop_table("favorites")

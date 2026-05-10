"""Add notification type and entity id

Revision ID: 008_notification_type_and_entity
Revises: 007_favorites
Create Date: 2026-05-10

"""

from alembic import op
import sqlalchemy as sa

revision = "008_notification_type_and_entity"
down_revision = "007_favorites"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("type", sa.String(length=64), nullable=True))
    op.add_column("notifications", sa.Column("entity_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("notifications", "entity_id")
    op.drop_column("notifications", "type")

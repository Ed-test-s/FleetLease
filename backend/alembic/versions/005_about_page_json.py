"""about_page_json on app_settings for About company CMS page

Revision ID: 005_about_page_json
Revises: 004_drop_bank_bic
"""

from alembic import op
import sqlalchemy as sa

revision = "005_about_page_json"
down_revision = "004_drop_bank_bic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_settings", sa.Column("about_page_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("app_settings", "about_page_json")

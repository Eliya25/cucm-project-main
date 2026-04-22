"""fix token_blacklist and add admin role

Revision ID: d015ea6f3030
Revises: 72da985a76df
Create Date: 2026-04-22 13:36:26.910069

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd015ea6f3030'
down_revision: Union[str, None] = '72da985a76df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. הוספת ADMIN ל-enum - חייב לרוץ לפני שאר השינויים
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")

    # 2. תיקון עמודות token_blacklist - החלפת expired_at ו-created_at ב-expires_at
    op.add_column('token_blacklist', sa.Column('expires_at', sa.DateTime(), nullable=True))

    # העתקת ערכים קיימים מ-expired_at ל-expires_at (אם יש שורות קיימות)
    op.execute("UPDATE token_blacklist SET expires_at = expired_at")

    # עכשיו הופכים ל-NOT NULL
    op.alter_column('token_blacklist', 'expires_at', nullable=False)

    # מחיקת עמודות ישנות
    op.drop_column('token_blacklist', 'created_at')
    op.drop_column('token_blacklist', 'expired_at')


def downgrade() -> None:
    op.add_column('token_blacklist', sa.Column(
        'expired_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False
    ))
    op.add_column('token_blacklist', sa.Column(
        'created_at', postgresql.TIMESTAMP(), server_default=sa.text('now()'),
        autoincrement=False, nullable=False
    ))
    op.execute("UPDATE token_blacklist SET expired_at = expires_at")
    op.drop_column('token_blacklist', 'expires_at')
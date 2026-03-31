"""rename ADMIN to SUPERADMIN in userrole enum

Revision ID: 4b19054e6b3c
Revises: b2bc318096ab
Create Date: 2026-03-31 20:00:04.292506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b19054e6b3c'
down_revision: Union[str, None] = 'b2bc318096ab'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename 'ADMIN' to 'SUPERADMIN' in the userrole enum
    op.execute("ALTER TYPE userrole RENAME VALUE 'ADMIN' TO 'SUPERADMIN';")


def downgrade() -> None:
    # Rename 'SUPERADMIN' back to 'ADMIN' in the userrole enum
    op.execute("ALTER TYPE userrole RENAME VALUE 'SUPERADMIN' TO 'ADMIN';")

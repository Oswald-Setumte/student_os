"""drop unique constraints on user names

Revision ID: d35d1dca64e8
Revises: 8e6780a6fbca
Create Date: 2026-11-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd35d1dca64e8'
down_revision: Union[str, Sequence[str], None] = '8e6780a6fbca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the unique constraints so different users can share a name."""
    op.drop_constraint('user_first_name_key', 'user', type_='unique')
    op.drop_constraint('user_last_name_key', 'user', type_='unique')


def downgrade() -> None:
    """Restore the unique constraints."""
    op.create_unique_constraint('user_first_name_key', 'user', ['first_name'])
    op.create_unique_constraint('user_last_name_key', 'user', ['last_name'])

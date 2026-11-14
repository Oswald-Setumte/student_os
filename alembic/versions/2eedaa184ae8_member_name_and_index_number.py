"""member name and index number

Revision ID: 2eedaa184ae8
Revises: 2cf1219697f5
Create Date: 2026-11-14 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2eedaa184ae8'
down_revision: Union[str, Sequence[str], None] = '2cf1219697f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename nickname to name and add a per-classroom index number."""
    op.alter_column(
        'classroom_member',
        'nickname',
        new_column_name='name',
        existing_type=sa.String(length=50),
        existing_nullable=True,
    )
    op.alter_column(
        'classroom_member',
        'name',
        type_=sa.String(length=100),
        existing_type=sa.String(length=50),
        existing_nullable=True,
    )
    op.add_column(
        'classroom_member', sa.Column('index_number', sa.String(length=50), nullable=True)
    )

    # Backfill older rows so the NOT NULL changes cannot fail.
    op.execute(
        """
        UPDATE classroom_member AS cm
        SET name = u.first_name || ' ' || u.last_name
        FROM "user" AS u
        WHERE cm.student_id = u.id AND (cm.name IS NULL OR cm.name = '')
        """
    )
    op.execute(
        """
        UPDATE classroom_member
        SET index_number = 'UNASSIGNED-' || id::text
        WHERE index_number IS NULL
        """
    )

    op.alter_column(
        'classroom_member',
        'name',
        existing_type=sa.String(length=100),
        nullable=False,
    )
    op.alter_column(
        'classroom_member',
        'index_number',
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.create_unique_constraint(
        'uq_classroom_member_classroom_index_number',
        'classroom_member',
        ['classroom_id', 'index_number'],
    )


def downgrade() -> None:
    """Drop the index number and restore nickname."""
    op.drop_constraint(
        'uq_classroom_member_classroom_index_number',
        'classroom_member',
        type_='unique',
    )
    op.alter_column(
        'classroom_member',
        'index_number',
        existing_type=sa.String(length=50),
        nullable=True,
    )
    op.drop_column('classroom_member', 'index_number')
    op.alter_column(
        'classroom_member',
        'name',
        existing_type=sa.String(length=100),
        nullable=True,
    )
    op.alter_column(
        'classroom_member',
        'name',
        type_=sa.String(length=50),
        existing_type=sa.String(length=100),
        existing_nullable=True,
    )
    op.alter_column(
        'classroom_member',
        'name',
        new_column_name='nickname',
        existing_type=sa.String(length=50),
        existing_nullable=True,
    )

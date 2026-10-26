"""Contrasena del personal (password_hash) para el login del dashboard.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('medical_staff', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(), nullable=True))



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('medical_staff', schema=None) as batch_op:
        batch_op.drop_column('password_hash')


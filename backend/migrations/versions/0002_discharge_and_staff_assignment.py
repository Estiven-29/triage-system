"""Alta de pacientes (discharged_at) y asignacion de personal (assigned_staff_id).

Reemplaza la columna assigned_to (texto libre que nunca se llenaba).

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('triage_assessments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_staff_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('discharged_at', sa.DateTime(), nullable=True))
        batch_op.create_index(batch_op.f('ix_triage_assessments_discharged_at'), ['discharged_at'], unique=False)
        batch_op.create_foreign_key('fk_triage_assessments_assigned_staff_id', 'medical_staff', ['assigned_staff_id'], ['id'])
        batch_op.drop_column('assigned_to')



def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('triage_assessments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_to', sa.VARCHAR(), nullable=True))
        batch_op.drop_constraint('fk_triage_assessments_assigned_staff_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_triage_assessments_discharged_at'))
        batch_op.drop_column('discharged_at')
        batch_op.drop_column('assigned_staff_id')


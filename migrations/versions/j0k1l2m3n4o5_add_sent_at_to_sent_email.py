"""add sent_at to sent_email

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-11-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j0k1l2m3n4o5'
down_revision = 'i9j0k1l2m3n4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('sent_email', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sent_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('sent_email', schema=None) as batch_op:
        batch_op.drop_column('sent_at')

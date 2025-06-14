"""Add xp_value to Question, rename experience to total_xp in User

Revision ID: 296a749a3ad0
Revises: 
Create Date: 2025-05-01 18:10:14.359536

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '296a749a3ad0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('question', schema=None) as batch_op:
        # Add server_default='10' for SQLite compatibility
        batch_op.add_column(sa.Column('xp_value', sa.Integer(), nullable=False, server_default='10'))

    with op.batch_alter_table('user', schema=None) as batch_op:
        # Add server_default='0' for SQLite compatibility
        batch_op.add_column(sa.Column('total_xp', sa.Integer(), nullable=False, server_default='0'))
        batch_op.alter_column('level',
               existing_type=sa.INTEGER(),
               nullable=False,
               # Also add server_default for level if it might be NULL initially
               server_default='1') 
        batch_op.drop_column('experience')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Add server_default='0' for the old experience column if needed for downgrade
        batch_op.add_column(sa.Column('experience', sa.INTEGER(), nullable=True, server_default='0'))
        batch_op.alter_column('level',
               existing_type=sa.INTEGER(),
               nullable=True,
               server_default=None) # Remove server_default on downgrade
        batch_op.drop_column('total_xp')

    with op.batch_alter_table('question', schema=None) as batch_op:
        batch_op.drop_column('xp_value')

    # ### end Alembic commands ###

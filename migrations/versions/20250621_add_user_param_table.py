"""
Migration: Add user_params table for storing param name, description, and required flag
"""
from alembic import op
import sqlalchemy as sa

# Alembic identifiers
revision = '20250621_add_user_param_table'
down_revision = 'f200f245867a'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'user_params',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('param_name', sa.String, nullable=False, unique=True),
        sa.Column('description', sa.String, nullable=True),
        sa.Column('required', sa.Boolean, nullable=False, default=True)
    )

def downgrade():
    op.drop_table('user_params')

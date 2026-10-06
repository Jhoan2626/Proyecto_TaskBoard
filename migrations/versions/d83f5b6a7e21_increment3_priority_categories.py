"""increment3_priority_categories

Revision ID: d83f5b6a7e21
Revises: c71e2a9f4b10
Create Date: 2026-10-05 23:10:00.000000

Incremento 3 (HU-07, HU-08): tabla `categories`, `tasks.priority` y
`tasks.category_id`. La migración original del Incremento 3 nunca llegó a
`main`, por lo que se encadena al final de la historia actual. Es aditiva y
tolera bases que ya tengan parte del esquema (por ejemplo creadas con
`db.create_all()`).
"""
from alembic import op
import sqlalchemy as sa


revision = 'd83f5b6a7e21'
down_revision = 'c71e2a9f4b10'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    if 'categories' not in inspector.get_table_names():
        op.create_table('categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_category_user_name')
        )
        with op.batch_alter_table('categories', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_categories_user_id'), ['user_id'], unique=False)

    task_columns = {column['name'] for column in inspector.get_columns('tasks')}
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        # Las tareas existentes quedan con la prioridad por defecto ('media').
        if 'priority' not in task_columns:
            batch_op.add_column(sa.Column('priority', sa.String(length=10), nullable=False, server_default='media'))
        if 'category_id' not in task_columns:
            batch_op.add_column(sa.Column('category_id', sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                'fk_tasks_category_id_categories', 'categories', ['category_id'], ['id'], ondelete='SET NULL'
            )


def downgrade():
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint('fk_tasks_category_id_categories', type_='foreignkey')
        batch_op.drop_column('category_id')
        batch_op.drop_column('priority')

    with op.batch_alter_table('categories', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_categories_user_id'))

    op.drop_table('categories')

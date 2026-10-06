"""increment5_task_order

Revision ID: c71e2a9f4b10
Revises: a4c0ab04c001
Create Date: 2026-10-05 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c71e2a9f4b10"
down_revision = "a4c0ab04c001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("position", sa.Integer(), nullable=True))

    connection = op.get_bind()
    tasks = connection.execute(
        sa.text(
            "SELECT id, user_id FROM tasks "
            "ORDER BY user_id, created_at DESC, id DESC"
        )
    ).mappings()

    positions = {}
    previous_user_id = None
    position = 0
    for task in tasks:
        if task["user_id"] != previous_user_id:
            previous_user_id = task["user_id"]
            position = 0
        positions[task["id"]] = position
        position += 1

    if positions:
        connection.execute(
            sa.text("UPDATE tasks SET position = :position WHERE id = :task_id"),
            [
                {"task_id": task_id, "position": task_position}
                for task_id, task_position in positions.items()
            ],
        )

    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.alter_column(
            "position",
            existing_type=sa.Integer(),
            nullable=False,
            server_default="0",
        )


def downgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_column("position")

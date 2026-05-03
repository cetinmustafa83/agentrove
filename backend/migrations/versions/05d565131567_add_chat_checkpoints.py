# Revision ID: 05d565131567
# Revises: b7fae3df7bca
# Create Date: 2026-05-03 02:06:33.241931

from typing import Sequence

from alembic import op
import sqlalchemy as sa
from app.db.migration_helpers import uuid_server_default, now_server_default
from app.db.types import GUID

# revision identifiers, used by Alembic.
revision: str = "05d565131567"
down_revision: str | None = "b7fae3df7bca"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_checkpoints",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("chat_id", GUID(), nullable=False),
        sa.Column("assistant_message_id", GUID(), nullable=False),
        sa.Column("cwd", sa.String(length=512), nullable=True),
        sa.Column("base_head", sa.String(length=64), nullable=False),
        sa.Column("pre_run_diff", sa.Text(), server_default="", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=now_server_default(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=now_server_default(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["assistant_message_id"], ["messages.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_chat_checkpoints_assistant_message_id",
        "chat_checkpoints",
        ["assistant_message_id"],
        unique=True,
    )
    op.create_index(
        "idx_chat_checkpoints_chat_id_created_at",
        "chat_checkpoints",
        ["chat_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_chat_checkpoints_chat_id_created_at",
        table_name="chat_checkpoints",
    )
    op.drop_index(
        "idx_chat_checkpoints_assistant_message_id",
        table_name="chat_checkpoints",
    )
    op.drop_table("chat_checkpoints")

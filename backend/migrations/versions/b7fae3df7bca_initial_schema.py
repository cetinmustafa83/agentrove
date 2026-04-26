# Revision ID: b7fae3df7bca
# Revises:
# Create Date: 2026-04-22 23:47:10.858160

from typing import Sequence

from alembic import op
import sqlalchemy as sa

from app.db.migration_helpers import now_server_default, uuid_server_default
from app.db.types import EncryptedString, GUID


revision: str = "b7fae3df7bca"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=256), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_superuser", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("verification_token", sa.String(length=128), nullable=True),
        sa.Column("verification_token_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reset_token", sa.String(length=128), nullable=True),
        sa.Column("reset_token_expires", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_refresh_token_user_revoked",
        "refresh_tokens",
        ["user_id", "revoked_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=False,
    )
    op.create_table(
        "user_settings",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("github_personal_access_token", EncryptedString(), nullable=True),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("custom_env_vars", sa.JSON(), nullable=True),
        sa.Column("personas", sa.JSON(), nullable=True),
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "workspaces",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("sandbox_id", sa.String(length=128), nullable=False),
        sa.Column(
            "sandbox_provider",
            sa.String(length=32),
            server_default="docker",
            nullable=False,
        ),
        sa.Column("workspace_path", sa.String(length=2048), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_workspaces_user_id_deleted_at",
        "workspaces",
        ["user_id", "deleted_at"],
        unique=False,
    )
    op.create_table(
        "chats",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("workspace_id", GUID(), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("session_agent_kind", sa.String(length=32), nullable=True),
        sa.Column("worktree_cwd", sa.String(length=512), nullable=True),
        sa.Column("context_token_usage", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_event_seq", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("parent_chat_id", GUID(), nullable=True),
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
        sa.ForeignKeyConstraint(["parent_chat_id"], ["chats.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chats_parent_chat_id", "chats", ["parent_chat_id"], unique=False)
    op.create_index(
        "idx_chats_user_id_deleted_at",
        "chats",
        ["user_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "idx_chats_user_id_updated_at_desc",
        "chats",
        ["user_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "idx_chats_workspace_id_deleted_at",
        "chats",
        ["workspace_id", "deleted_at"],
        unique=False,
    )
    op.create_table(
        "messages",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("chat_id", GUID(), nullable=False),
        sa.Column("content_text", sa.Text(), server_default="", nullable=False),
        sa.Column("content_render", sa.JSON(), server_default='{"events": []}', nullable=False),
        sa.Column("last_seq", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("active_stream_id", GUID(), nullable=True),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", name="messagerole"),
            nullable=False,
        ),
        sa.Column("model_id", sa.String(length=128), nullable=True),
        sa.Column("session_id", sa.String(length=128), nullable=True),
        sa.Column("total_cost_usd", sa.Float(), server_default="0.0", nullable=True),
        sa.Column(
            "stream_status",
            sa.Enum(
                "in_progress",
                "completed",
                "failed",
                "interrupted",
                name="messagestreamstatus",
            ),
            server_default="in_progress",
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_chat_id_created_at",
        "messages",
        ["chat_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_messages_chat_id_deleted_at",
        "messages",
        ["chat_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "idx_messages_chat_id_role_deleted",
        "messages",
        ["chat_id", "role", "deleted_at"],
        unique=False,
    )
    op.create_index("idx_messages_role_created", "messages", ["role", "created_at"], unique=False)
    op.create_table(
        "message_attachments",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("file_url", sa.String(length=2048), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column(
            "file_type",
            sa.Enum("image", "pdf", "xlsx", name="attachmenttype"),
            server_default="image",
            nullable=False,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
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
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_message_attachments_message_id"),
        "message_attachments",
        ["message_id"],
        unique=False,
    )
    op.create_table(
        "message_events",
        sa.Column("id", GUID(), server_default=uuid_server_default(), nullable=False),
        sa.Column("message_id", GUID(), nullable=False),
        sa.Column("chat_id", GUID(), nullable=False),
        sa.Column("stream_id", GUID(), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("render_payload", sa.JSON(), nullable=False),
        sa.Column("audit_payload", sa.JSON(), nullable=True),
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
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_message_events_chat_id_created_at",
        "message_events",
        ["chat_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_message_events_chat_id_stream_id_seq",
        "message_events",
        ["chat_id", "stream_id", "seq"],
        unique=False,
    )
    op.create_index(
        "idx_message_events_message_id_seq",
        "message_events",
        ["message_id", "seq"],
        unique=False,
    )
    op.create_index(
        "uq_message_events_stream_seq",
        "message_events",
        ["stream_id", "seq"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_message_events_stream_seq", table_name="message_events")
    op.drop_index("idx_message_events_message_id_seq", table_name="message_events")
    op.drop_index("idx_message_events_chat_id_stream_id_seq", table_name="message_events")
    op.drop_index("idx_message_events_chat_id_created_at", table_name="message_events")
    op.drop_table("message_events")
    op.drop_index(op.f("ix_message_attachments_message_id"), table_name="message_attachments")
    op.drop_table("message_attachments")
    op.drop_index("idx_messages_role_created", table_name="messages")
    op.drop_index("idx_messages_chat_id_role_deleted", table_name="messages")
    op.drop_index("idx_messages_chat_id_deleted_at", table_name="messages")
    op.drop_index("idx_messages_chat_id_created_at", table_name="messages")
    op.drop_table("messages")
    op.drop_index("idx_chats_workspace_id_deleted_at", table_name="chats")
    op.drop_index("idx_chats_user_id_updated_at_desc", table_name="chats")
    op.drop_index("idx_chats_user_id_deleted_at", table_name="chats")
    op.drop_index("idx_chats_parent_chat_id", table_name="chats")
    op.drop_table("chats")
    op.drop_index("idx_workspaces_user_id_deleted_at", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_table("user_settings")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_index("idx_refresh_token_user_revoked", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import tests.bootstrap
from app.models.db_models.chat import Chat, Message, MessageAttachment
from app.models.db_models.enums import AttachmentType, MessageRole, MessageStreamStatus
from app.models.db_models.user import User
from app.models.db_models.workspace import Workspace

from tests.conftest import LoginClient, UserFactory
from tests.helpers import create_authenticated_workspace


pytestmark = pytest.mark.anyio


async def create_attachment_row(
    db_session: AsyncSession,
    user: User,
    workspace: Workspace,
    *,
    file_path: str,
    filename: str = "notes.txt",
) -> MessageAttachment:
    chat = Chat(
        title="Attachment Chat",
        user_id=user.id,
        workspace_id=workspace.id,
    )
    db_session.add(chat)
    await db_session.flush()

    message = Message(
        chat_id=chat.id,
        content_text="See attachment",
        content_render={"events": [{"type": "user_text", "text": "See attachment"}]},
        role=MessageRole.USER,
        stream_status=MessageStreamStatus.COMPLETED,
    )
    db_session.add(message)
    await db_session.flush()

    attachment = MessageAttachment(
        message_id=message.id,
        file_url="/api/v1/attachments/pending/preview",
        file_path=file_path,
        file_type=AttachmentType.PDF,
        filename=filename,
    )
    db_session.add(attachment)
    await db_session.commit()
    await db_session.refresh(attachment)
    return attachment


def storage_path(*parts: str) -> Path:
    return tests.bootstrap.TEST_DIR.joinpath("storage", *parts)


async def test_attachment_preview_and_download_serve_owned_file(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    file_path = storage_path("attachments", str(user.id), "notes.txt")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("attachment body", encoding="utf-8")
    attachment = await create_attachment_row(
        db_session,
        user,
        workspace,
        file_path=str(file_path.relative_to(storage_path())),
    )

    preview_response = await client.get(
        f"/api/v1/attachments/{attachment.id}/preview", headers=headers
    )
    download_response = await client.get(
        f"/api/v1/attachments/{attachment.id}/download", headers=headers
    )

    assert preview_response.status_code == 200
    assert preview_response.text == "attachment body"
    assert preview_response.headers["cache-control"] == "private, max-age=3600"
    assert preview_response.headers["content-disposition"].startswith("inline;")
    assert download_response.status_code == 200
    assert download_response.text == "attachment body"
    assert download_response.headers["content-disposition"].startswith("attachment;")


async def test_attachment_preview_rejects_other_user(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    owner_headers, owner, workspace = await create_authenticated_workspace(
        db_session,
        create_user,
        login,
        email="attachment-owner@example.com",
        username="attachmentowner",
    )
    other_headers, _other_user, _other_workspace = await create_authenticated_workspace(
        db_session,
        create_user,
        login,
        email="attachment-other@example.com",
        username="attachmentother",
    )
    file_path = storage_path("attachments", str(owner.id), "private.txt")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("private attachment", encoding="utf-8")
    attachment = await create_attachment_row(
        db_session,
        owner,
        workspace,
        file_path=str(file_path.relative_to(storage_path())),
        filename="private.txt",
    )

    owner_response = await client.get(
        f"/api/v1/attachments/{attachment.id}/preview", headers=owner_headers
    )
    other_response = await client.get(
        f"/api/v1/attachments/{attachment.id}/preview", headers=other_headers
    )

    assert owner_response.status_code == 200
    assert other_response.status_code == 403
    assert other_response.json()["detail"] == "Access denied"


async def test_attachment_preview_returns_404_for_missing_file(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    attachment = await create_attachment_row(
        db_session,
        user,
        workspace,
        file_path=f"attachments/{user.id}/missing.txt",
        filename="missing.txt",
    )

    response = await client.get(
        f"/api/v1/attachments/{attachment.id}/preview", headers=headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"


async def test_temp_attachment_preview_allows_only_current_user_temp_dir(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, _workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    temp_file = storage_path("temp", str(user.id), "draft.txt")
    temp_file.parent.mkdir(parents=True, exist_ok=True)
    temp_file.write_text("draft attachment", encoding="utf-8")
    other_temp_file = storage_path("temp", "other-user", "draft.txt")
    other_temp_file.parent.mkdir(parents=True, exist_ok=True)
    other_temp_file.write_text("other draft", encoding="utf-8")

    preview_response = await client.get(
        "/api/v1/attachments/temp/preview",
        params={"path": str(temp_file.relative_to(storage_path()))},
        headers=headers,
    )
    other_response = await client.get(
        "/api/v1/attachments/temp/preview",
        params={"path": str(other_temp_file.relative_to(storage_path()))},
        headers=headers,
    )
    traversal_response = await client.get(
        "/api/v1/attachments/temp/preview",
        params={"path": f"temp/{user.id}/../other-user/draft.txt"},
        headers=headers,
    )

    assert preview_response.status_code == 200
    assert preview_response.text == "draft attachment"
    assert preview_response.headers["content-disposition"].startswith("inline;")
    assert other_response.status_code == 403
    assert traversal_response.status_code == 403

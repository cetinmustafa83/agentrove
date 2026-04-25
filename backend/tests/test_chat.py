from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.chat import Chat, Message
from app.models.db_models.enums import MessageRole, MessageStreamStatus
from app.models.db_models.user import User
from app.models.db_models.workspace import Workspace

from tests.conftest import LoginClient, UserFactory


TEST_MODEL_ID = "opencode:google-vertex-anthropic/claude-sonnet-4-5@20250929"

pytestmark = pytest.mark.anyio


async def create_authenticated_workspace(
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
    *,
    email: str = "chat@example.com",
    username: str = "chatuser",
    workspace_name: str = "Chat Workspace",
) -> tuple[dict[str, str], User, Workspace]:
    user = await create_user(email=email, username=username)
    tokens = await login(email=email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    workspace = Workspace(
        name=workspace_name,
        user_id=user.id,
        sandbox_id=f"sandbox-{username}",
        sandbox_provider="host",
        workspace_path=f"/tmp/agentrove-test-{username}",
        source_type="empty",
        source_url=None,
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return headers, user, workspace


async def create_chat_row(
    db_session: AsyncSession,
    user: User,
    workspace: Workspace,
    *,
    title: str = "Existing Chat",
) -> Chat:
    chat = Chat(
        title=title,
        user_id=user.id,
        workspace_id=workspace.id,
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)
    return chat


async def create_message_row(
    db_session: AsyncSession,
    chat: Chat,
    *,
    content: str,
    role: MessageRole = MessageRole.USER,
) -> Message:
    message = Message(
        chat_id=chat.id,
        content_text=content,
        content_render={"events": [{"type": "user_text", "text": content}]},
        role=role,
        stream_status=MessageStreamStatus.COMPLETED,
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message


async def test_create_list_and_get_chat(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )

    create_response = await client.post(
        "/api/v1/chat/chats",
        json={
            "title": "New Chat",
            "model_id": TEST_MODEL_ID,
            "workspace_id": str(workspace.id),
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["title"] == "New Chat"
    assert created["user_id"] == str(user.id)
    assert created["workspace_id"] == str(workspace.id)
    assert created["sandbox_id"] == workspace.sandbox_id
    assert created["sub_thread_count"] == 0

    list_response = await client.get("/api/v1/chat/chats", headers=headers)
    detail_response = await client.get(
        f"/api/v1/chat/chats/{created['id']}", headers=headers
    )

    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == created["id"]
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == created["id"]


async def test_chat_access_is_limited_to_owner(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    owner_headers, owner, workspace = await create_authenticated_workspace(
        db_session,
        create_user,
        login,
        email="owner-chat@example.com",
        username="ownerchat",
    )
    chat = await create_chat_row(db_session, owner, workspace)
    other_headers, _other_user, _other_workspace = await create_authenticated_workspace(
        db_session,
        create_user,
        login,
        email="other-chat@example.com",
        username="otherchat",
    )

    other_list = await client.get("/api/v1/chat/chats", headers=other_headers)
    other_get = await client.get(f"/api/v1/chat/chats/{chat.id}", headers=other_headers)
    owner_get = await client.get(f"/api/v1/chat/chats/{chat.id}", headers=owner_headers)

    assert other_list.status_code == 200
    assert other_list.json()["items"] == []
    assert other_get.status_code == 404
    assert owner_get.status_code == 200


async def test_update_chat_title_and_pin_filters(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    chat = await create_chat_row(db_session, user, workspace, title="Original")
    await create_chat_row(db_session, user, workspace, title="Unpinned")

    update_response = await client.patch(
        f"/api/v1/chat/chats/{chat.id}",
        json={"title": "Renamed", "pinned": True},
        headers=headers,
    )
    pinned_response = await client.get(
        "/api/v1/chat/chats?pinned=true", headers=headers
    )
    unpinned_response = await client.get(
        "/api/v1/chat/chats?pinned=false", headers=headers
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["title"] == "Renamed"
    assert updated["pinned_at"] is not None
    assert pinned_response.status_code == 200
    assert [item["id"] for item in pinned_response.json()["items"]] == [str(chat.id)]
    assert unpinned_response.status_code == 200
    assert unpinned_response.json()["total"] == 1


async def test_delete_chat_excludes_it_from_list_and_detail(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    chat = await create_chat_row(db_session, user, workspace, title="Delete Me")
    remaining = await create_chat_row(db_session, user, workspace, title="Keep Me")

    delete_response = await client.delete(
        f"/api/v1/chat/chats/{chat.id}", headers=headers
    )
    list_response = await client.get("/api/v1/chat/chats", headers=headers)
    detail_response = await client.get(f"/api/v1/chat/chats/{chat.id}", headers=headers)

    assert delete_response.status_code == 204
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()["items"]] == [str(remaining.id)]
    assert detail_response.status_code == 404


async def test_sub_threads_are_listed_and_nested_sub_threads_are_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    parent = await create_chat_row(db_session, user, workspace, title="Parent")

    create_sub_response = await client.post(
        "/api/v1/chat/chats",
        json={
            "title": "Sub-thread",
            "model_id": TEST_MODEL_ID,
            "workspace_id": str(workspace.id),
            "parent_chat_id": str(parent.id),
        },
        headers=headers,
    )
    sub_thread = create_sub_response.json()
    list_response = await client.get(
        f"/api/v1/chat/chats/{parent.id}/sub-threads", headers=headers
    )
    nested_response = await client.post(
        "/api/v1/chat/chats",
        json={
            "title": "Nested",
            "model_id": TEST_MODEL_ID,
            "workspace_id": str(workspace.id),
            "parent_chat_id": sub_thread["id"],
        },
        headers=headers,
    )

    assert create_sub_response.status_code == 201
    assert sub_thread["workspace_id"] == str(workspace.id)
    assert sub_thread["parent_chat_id"] == str(parent.id)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [sub_thread["id"]]
    assert nested_response.status_code == 400
    assert nested_response.json()["detail"] == (
        "Cannot create a sub-thread of a sub-thread"
    )


async def test_chat_messages_returns_only_owned_chat_messages(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    chat = await create_chat_row(db_session, user, workspace)
    message = await create_message_row(db_session, chat, content="Visible message")
    other_headers, _other_user, _other_workspace = await create_authenticated_workspace(
        db_session,
        create_user,
        login,
        email="messages-other@example.com",
        username="messagesother",
    )

    response = await client.get(
        f"/api/v1/chat/chats/{chat.id}/messages", headers=headers
    )
    other_response = await client.get(
        f"/api/v1/chat/chats/{chat.id}/messages", headers=other_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_more"] is False
    assert body["next_cursor"] is None
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == str(message.id)
    assert body["items"][0]["content_text"] == "Visible message"
    assert other_response.status_code == 403


async def test_search_chats_returns_matches_and_rejects_blank_query(
    client: AsyncClient,
    db_session: AsyncSession,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    headers, user, workspace = await create_authenticated_workspace(
        db_session, create_user, login
    )
    chat = await create_chat_row(db_session, user, workspace, title="Searchable Chat")
    message = await create_message_row(
        db_session,
        chat,
        content="The agent found a durable needle in the transcript.",
    )
    await create_message_row(db_session, chat, content="Unrelated message")

    response = await client.get("/api/v1/chat/chats/search?q=needle", headers=headers)
    blank_response = await client.get(
        "/api/v1/chat/chats/search?q=%20%20", headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["truncated"] is False
    assert len(body["results"]) == 1
    result = body["results"][0]
    assert result["chat_id"] == str(chat.id)
    assert result["chat_title"] == "Searchable Chat"
    assert result["workspace_id"] == str(workspace.id)
    assert result["workspace_name"] == workspace.name
    assert result["match_count"] == 1
    assert result["matches"][0]["message_id"] == str(message.id)
    assert result["matches"][0]["snippet_match"] == "needle"
    assert blank_response.status_code == 422


async def test_chats_reject_missing_token(client: AsyncClient) -> None:
    chat_id = UUID("00000000-0000-0000-0000-000000000001")

    list_response = await client.get("/api/v1/chat/chats")
    create_response = await client.post(
        "/api/v1/chat/chats",
        json={
            "title": "No Auth",
            "model_id": TEST_MODEL_ID,
            "workspace_id": str(chat_id),
        },
    )
    detail_response = await client.get(f"/api/v1/chat/chats/{chat_id}")

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert detail_response.status_code == 401

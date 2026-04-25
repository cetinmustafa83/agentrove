from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.services.sandbox_providers.base import SandboxProvider
from app.services.sandbox_providers.types import (
    CommandResult,
    FileContent,
    FileMetadata,
    PtyDataCallbackType,
    PtySession,
    PtySize,
)

from tests.conftest import LoginClient, UserFactory


pytestmark = pytest.mark.anyio


class FakeSandboxProvider(SandboxProvider):
    def __init__(self, workspace_path: str | None = None) -> None:
        self._workspace_root = workspace_path or "/tmp/agentrove-test-workspace"

    @property
    def workspace_root(self) -> str:
        return self._workspace_root

    async def create_sandbox(self, workspace_path: str | None = None) -> str:
        return "sandbox-1"

    async def delete_sandbox(self, sandbox_id: str) -> None:
        return None

    async def execute_command(
        self,
        sandbox_id: str,
        command: str,
        envs: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> CommandResult:
        return CommandResult(stdout="", stderr="", exit_code=0)

    async def write_file(
        self,
        sandbox_id: str,
        path: str,
        content: str | bytes,
    ) -> None:
        return None

    async def read_file(
        self,
        sandbox_id: str,
        path: str,
    ) -> FileContent:
        return FileContent(path=path, content="", type="file", is_binary=False)

    async def list_files(
        self,
        sandbox_id: str,
        path: str = "",
    ) -> list[FileMetadata]:
        return []

    async def create_pty(
        self,
        sandbox_id: str,
        rows: int,
        cols: int,
        tmux_session: str,
        on_data: PtyDataCallbackType | None = None,
    ) -> PtySession:
        return PtySession(id="pty-1", pid=None, rows=rows, cols=cols)

    async def send_pty_input(
        self,
        sandbox_id: str,
        pty_id: str,
        data: bytes,
    ) -> None:
        return None

    async def resize_pty(
        self,
        sandbox_id: str,
        pty_id: str,
        size: PtySize,
    ) -> None:
        return None

    async def kill_pty(self, sandbox_id: str, pty_id: str) -> None:
        return None


def _fake_create_provider(
    provider_type: str,
    workspace_path: str | None = None,
) -> FakeSandboxProvider:
    return FakeSandboxProvider(workspace_path=workspace_path)


@pytest.fixture
def workspace_sandbox(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(SandboxProvider, "create_provider", _fake_create_provider)


async def create_authenticated_workspace(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    *,
    email: str = "workspace@example.com",
    username: str = "workspaceuser",
    name: str = "Test Workspace",
) -> tuple[dict[str, str], dict[str, Any]]:
    await create_user(email=email, username=username)
    tokens = await login(email=email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    response = await client.post(
        "/api/v1/workspaces",
        json={"name": name, "source_type": "empty", "sandbox_provider": "host"},
        headers=headers,
    )

    assert response.status_code == 201
    return headers, response.json()


async def test_create_workspace_persists_empty_workspace(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    workspace_sandbox: None,
) -> None:
    user = await create_user(email="create-workspace@example.com", username="createws")
    tokens = await login(email="create-workspace@example.com")

    response = await client.post(
        "/api/v1/workspaces",
        json={
            "name": "New Workspace",
            "source_type": "empty",
            "sandbox_provider": "host",
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "New Workspace"
    assert body["user_id"] == str(user.id)
    assert body["sandbox_id"] == "sandbox-1"
    assert body["sandbox_provider"] == "host"
    assert body["source_type"] == "empty"
    assert body["source_url"] is None
    assert Path(body["workspace_path"]).is_dir()


async def test_list_get_and_update_workspace(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    workspace_sandbox: None,
) -> None:
    headers, workspace = await create_authenticated_workspace(
        client, create_user, login, name="Original Name"
    )
    workspace_id = workspace["id"]

    list_response = await client.get("/api/v1/workspaces", headers=headers)
    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=headers
    )
    update_response = await client.patch(
        f"/api/v1/workspaces/{workspace_id}",
        json={"name": "Renamed Workspace"},
        headers=headers,
    )

    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["total"] == 1
    assert listed["items"][0]["id"] == workspace_id
    assert listed["items"][0]["chat_count"] == 0
    assert listed["items"][0]["last_chat_at"] is None
    assert get_response.status_code == 200
    assert get_response.json()["id"] == workspace_id
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Renamed Workspace"


async def test_workspace_access_is_limited_to_owner(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    workspace_sandbox: None,
) -> None:
    owner_headers, workspace = await create_authenticated_workspace(
        client,
        create_user,
        login,
        email="owner@example.com",
        username="owneruser",
    )
    await create_user(email="other@example.com", username="otheruser")
    other_tokens = await login(email="other@example.com")
    other_headers = {"Authorization": f"Bearer {other_tokens['access_token']}"}
    workspace_id = workspace["id"]

    other_list = await client.get("/api/v1/workspaces", headers=other_headers)
    other_get = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=other_headers
    )
    owner_get = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=owner_headers
    )

    assert other_list.status_code == 200
    assert other_list.json()["items"] == []
    assert other_get.status_code == 404
    assert owner_get.status_code == 200


async def test_delete_workspace_soft_deletes_it(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    workspace_sandbox: None,
) -> None:
    headers, workspace = await create_authenticated_workspace(
        client, create_user, login
    )
    workspace_id = workspace["id"]

    response = await client.delete(
        f"/api/v1/workspaces/{workspace_id}", headers=headers
    )
    list_response = await client.get("/api/v1/workspaces", headers=headers)
    get_response = await client.get(
        f"/api/v1/workspaces/{workspace_id}", headers=headers
    )

    assert response.status_code == 204
    assert list_response.status_code == 200
    assert list_response.json()["items"] == []
    assert get_response.status_code == 404


async def test_create_workspace_rejects_invalid_git_payload(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
    workspace_sandbox: None,
) -> None:
    await create_user(email="git-workspace@example.com", username="gitworkspace")
    tokens = await login(email="git-workspace@example.com")

    response = await client.post(
        "/api/v1/workspaces",
        json={
            "name": "Git Workspace",
            "source_type": "git",
            "sandbox_provider": "host",
        },
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "git_url is required for git workspace"


async def test_workspaces_reject_missing_token(client: AsyncClient) -> None:
    workspace_id = UUID("00000000-0000-0000-0000-000000000001")

    list_response = await client.get("/api/v1/workspaces")
    create_response = await client.post(
        "/api/v1/workspaces",
        json={"name": "No Auth", "source_type": "empty", "sandbox_provider": "host"},
    )
    get_response = await client.get(f"/api/v1/workspaces/{workspace_id}")

    assert list_response.status_code == 401
    assert create_response.status_code == 401
    assert get_response.status_code == 401

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.user import User

from tests.conftest import EmailCapture, LoginClient, SettingsOverride, UserFactory
from tests.helpers import count_refresh_tokens, get_user_by_email, get_user_settings


pytestmark = pytest.mark.anyio


async def test_register_creates_user_and_settings(
    client: AsyncClient,
    db_session: AsyncSession,
    email_capture: EmailCapture,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["username"] == "newuser"
    assert body["email_verification_required"] is False

    user = await get_user_by_email(db_session, "new@example.com")
    assert user is not None
    assert await get_user_settings(db_session, user.id) is not None


async def test_register_rejects_duplicate_email(
    client: AsyncClient,
    create_user: UserFactory,
    email_capture: EmailCapture,
) -> None:
    await create_user(email="taken@example.com", username="existing")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "taken@example.com",
            "username": "newuser",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


async def test_register_rejects_duplicate_username(
    client: AsyncClient,
    create_user: UserFactory,
    email_capture: EmailCapture,
) -> None:
    await create_user(email="first@example.com", username="takenname")

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "second@example.com",
            "username": "takenname",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"


async def test_register_rejects_invalid_username(
    client: AsyncClient,
    email_capture: EmailCapture,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid@example.com",
            "username": "_bad",
            "password": "password123",
        },
    )

    assert response.status_code == 422


async def test_register_rejects_disabled_registration(
    client: AsyncClient,
    settings_override: SettingsOverride,
    email_capture: EmailCapture,
) -> None:
    settings_override(REGISTRATION_DISABLED=True)

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "blocked@example.com",
            "username": "blocked",
            "password": "password123",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Registration is disabled"


async def test_register_rejects_disposable_email(
    client: AsyncClient,
    settings_override: SettingsOverride,
    email_capture: EmailCapture,
) -> None:
    settings_override(BLOCK_DISPOSABLE_EMAILS=True)
    email_capture.disposable = True

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "username": "newuser",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Disposable email addresses are not allowed. Please use a permanent email address."
    )


async def test_login_returns_access_and_refresh_tokens(
    client: AsyncClient,
    create_user: UserFactory,
    db_session: AsyncSession,
) -> None:
    user = await create_user(email="login@example.com", username="loginuser")

    response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "login@example.com", "password": "password123"},
        headers={"user-agent": "pytest"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert await count_refresh_tokens(db_session, user.id) == 1


async def test_login_rejects_wrong_password(
    client: AsyncClient,
    create_user: UserFactory,
) -> None:
    await create_user(email="login@example.com", username="loginuser")

    response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "login@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_rejects_inactive_user(
    client: AsyncClient,
    create_user: UserFactory,
) -> None:
    await create_user(
        email="inactive@example.com",
        username="inactive",
        is_active=False,
    )

    response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "inactive@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Account is inactive"


async def test_login_rejects_unverified_user_when_verification_required(
    client: AsyncClient,
    create_user: UserFactory,
    settings_override: SettingsOverride,
) -> None:
    settings_override(REQUIRE_EMAIL_VERIFICATION=True)
    await create_user(
        email="unverified@example.com",
        username="unverified",
        is_verified=False,
    )

    response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "unverified@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Please verify your email before logging in"


async def test_me_returns_current_user(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    await create_user(email="me@example.com", username="meuser")
    tokens = await login(email="me@example.com")

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["username"] == "meuser"
    assert body["is_verified"] is True


async def test_me_rejects_missing_token(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_refresh_rotates_refresh_token(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    await create_user(email="refresh@example.com", username="refreshuser")
    tokens = await login(email="refresh@example.com")

    response = await client.post(
        "/api/v1/auth/jwt/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != tokens["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_refresh_rejects_rotated_token(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    await create_user(email="refresh@example.com", username="refreshuser")
    tokens = await login(email="refresh@example.com")
    await client.post(
        "/api/v1/auth/jwt/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    response = await client.post(
        "/api/v1/auth/jwt/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


async def test_refresh_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/jwt/refresh",
        json={"refresh_token": "not-a-real-refresh-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


async def test_logout_revokes_refresh_token(
    client: AsyncClient,
    create_user: UserFactory,
    login: LoginClient,
) -> None:
    await create_user(email="logout@example.com", username="logoutuser")
    tokens = await login(email="logout@example.com")

    response = await client.post(
        "/api/v1/auth/jwt/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == 204
    refresh_response = await client.post(
        "/api/v1/auth/jwt/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


async def test_forgot_password_sends_reset_email(
    client: AsyncClient,
    create_user: UserFactory,
    email_capture: EmailCapture,
) -> None:
    await create_user(email="reset@example.com", username="resetuser")

    response = await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )

    assert response.status_code == 202
    assert len(email_capture.password_reset) == 1
    assert email_capture.password_reset[0]["email"] == "reset@example.com"
    assert email_capture.password_reset[0]["token"]


async def test_reset_password_accepts_valid_token(
    client: AsyncClient,
    create_user: UserFactory,
    email_capture: EmailCapture,
) -> None:
    await create_user(email="reset@example.com", username="resetuser")
    await client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    token = email_capture.password_reset[0]["token"]

    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "password": "newpassword123"},
    )

    assert response.status_code == 200
    login_response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "reset@example.com", "password": "newpassword123"},
    )
    assert login_response.status_code == 200


async def test_reset_password_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalid-token", "password": "newpassword123"},
    )

    assert response.status_code == 400


async def test_request_verify_token_sends_verification_email(
    client: AsyncClient,
    create_user: UserFactory,
    email_capture: EmailCapture,
) -> None:
    await create_user(
        email="verify@example.com",
        username="verifyuser",
        is_verified=False,
    )

    response = await client.post(
        "/api/v1/auth/request-verify-token",
        json={"email": "verify@example.com"},
    )

    assert response.status_code == 202
    assert len(email_capture.verification) == 1
    assert email_capture.verification[0]["email"] == "verify@example.com"
    assert email_capture.verification[0]["token"]


async def test_verify_accepts_valid_token(
    client: AsyncClient,
    create_user: UserFactory,
    db_session: AsyncSession,
    email_capture: EmailCapture,
) -> None:
    user: User = await create_user(
        email="verify@example.com",
        username="verifyuser",
        is_verified=False,
    )
    await client.post(
        "/api/v1/auth/request-verify-token",
        json={"email": "verify@example.com"},
    )
    token = email_capture.verification[0]["token"]

    response = await client.post("/api/v1/auth/verify", json={"token": token})

    assert response.status_code == 200
    await db_session.refresh(user)
    assert user.is_verified is True


async def test_verify_rejects_invalid_token(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/verify", json={"token": "bad-token"})

    assert response.status_code == 400

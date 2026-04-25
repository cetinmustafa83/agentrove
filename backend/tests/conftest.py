from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

import tests.bootstrap
from app.api.endpoints import auth as auth_endpoint
from app.core.config import get_settings
from app.core.security import get_password_hash
from app.db.base_class import Base
from app.db.session import SessionLocal, engine
from app.main import create_application
from app.models.db_models.user import User, UserSettings
from app.services.email import email_service

TEST_DIR = tests.bootstrap.TEST_DIR


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def database() -> AsyncIterator[None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def app() -> Any:
    auth_endpoint.limiter.enabled = False
    TEST_DIR.joinpath("storage").mkdir(exist_ok=True)
    application = create_application()
    yield application
    application.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: Any) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app, client=("testclient", 50000))
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


@dataclass
class EmailCapture:
    disposable: bool = False
    verification: list[dict[str, Any]] = field(default_factory=list)
    password_reset: list[dict[str, Any]] = field(default_factory=list)


@pytest.fixture
def email_capture(monkeypatch: pytest.MonkeyPatch) -> EmailCapture:
    capture = EmailCapture()

    async def is_disposable_email(_email: str) -> bool:
        return capture.disposable

    async def send_verification_email(
        email: str, verification_token: str, user_name: str | None = None
    ) -> bool:
        capture.verification.append(
            {"email": email, "token": verification_token, "user_name": user_name}
        )
        return True

    async def send_password_reset_email(
        email: str, reset_token: str, user_name: str | None = None
    ) -> bool:
        capture.password_reset.append(
            {"email": email, "token": reset_token, "user_name": user_name}
        )
        return True

    monkeypatch.setattr(email_service, "is_disposable_email", is_disposable_email)
    monkeypatch.setattr(
        email_service, "send_verification_email", send_verification_email
    )
    monkeypatch.setattr(
        email_service, "send_password_reset_email", send_password_reset_email
    )
    return capture


@pytest.fixture
def settings_override() -> Iterator[Callable[..., None]]:
    settings = get_settings()
    original = {
        "REGISTRATION_DISABLED": settings.REGISTRATION_DISABLED,
        "REQUIRE_EMAIL_VERIFICATION": settings.REQUIRE_EMAIL_VERIFICATION,
        "BLOCK_DISPOSABLE_EMAILS": settings.BLOCK_DISPOSABLE_EMAILS,
    }

    def apply(**values: bool) -> None:
        for key, value in values.items():
            setattr(settings, key, value)

    yield apply

    for key, value in original.items():
        setattr(settings, key, value)


@pytest_asyncio.fixture
async def create_user(
    db_session: AsyncSession,
) -> Callable[..., Awaitable[User]]:
    async def create(
        *,
        email: str = "user@example.com",
        username: str = "testuser",
        password: str = "password123",
        is_active: bool = True,
        is_verified: bool = True,
    ) -> User:
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_active=is_active,
            is_verified=is_verified,
            is_superuser=False,
        )
        db_session.add(user)
        await db_session.flush()
        db_session.add(
            UserSettings(
                user_id=user.id,
                github_personal_access_token=None,
            )
        )
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return create


@pytest_asyncio.fixture
async def login(
    client: httpx.AsyncClient,
) -> Callable[..., Awaitable[dict[str, str]]]:
    async def authenticate(
        *,
        email: str = "user@example.com",
        password: str = "password123",
    ) -> dict[str, str]:
        response = await client.post(
            "/api/v1/auth/jwt/login",
            data={"username": email, "password": password},
        )
        assert response.status_code == 200
        return response.json()

    return authenticate

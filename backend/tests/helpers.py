from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models.refresh_token import RefreshToken
from app.models.db_models.user import User, UserSettings


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_settings(db: AsyncSession, user_id: Any) -> UserSettings | None:
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def count_refresh_tokens(db: AsyncSession, user_id: Any) -> int:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.user_id == user_id)
    )
    return len(result.scalars().all())

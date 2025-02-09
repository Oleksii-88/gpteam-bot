from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

class UserService:
    @staticmethod
    async def get_user_by_telegram_id(db: AsyncSession, telegram_id: str) -> User:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(db: AsyncSession, telegram_id: str, username: str = None, first_name: str = None) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            status="pending"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_user_status(db: AsyncSession, telegram_id: str, status: str) -> User:
        user = await UserService.get_user_by_telegram_id(db, telegram_id)
        if user:
            user.status = status
            await db.commit()
            await db.refresh(user)
        return user

    @staticmethod
    async def get_pending_users(db: AsyncSession):
        result = await db.execute(
            select(User).where(User.status == "pending")
        )
        return result.scalars().all()

    @staticmethod
    async def set_admin(db: AsyncSession, telegram_id: str, is_admin: bool = True) -> User:
        user = await UserService.get_user_by_telegram_id(db, telegram_id)
        if user:
            user.is_admin = is_admin
            await db.commit()
            await db.refresh(user)
        return user

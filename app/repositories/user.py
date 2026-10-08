"""Запросы к базе по учётным записям."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_login(self, login: str) -> User | None:
        stmt = select(User).where(User.login == login)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self) -> int:
        """Нужен при старте: если пусто, создаём первого администратора."""
        stmt = select(func.count()).select_from(User)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

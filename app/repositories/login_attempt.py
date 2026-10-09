"""Запросы к таблице неудачных попыток входа."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def count_recent(self, ip: str, window_minutes: int) -> int:
        since = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
        stmt = select(func.count()).where(
            LoginAttempt.ip == ip, LoginAttempt.attempted_at >= since
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def add(self, ip: str, login: str) -> None:
        self.session.add(LoginAttempt(ip=ip, login=login[:160]))

    async def clear_for(self, ip: str) -> None:
        """После удачного входа счётчик для адреса обнуляется."""
        await self.session.execute(delete(LoginAttempt).where(LoginAttempt.ip == ip))

    async def purge_older_than(self, minutes: int) -> None:
        """Чистим хвост, иначе таблица будет расти вечно.

        Вызывается при удачном входе: момент редкий, запрос дешёвый,
        а отдельное задание по расписанию ради этого заводить незачем.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        await self.session.execute(
            delete(LoginAttempt).where(LoginAttempt.attempted_at < cutoff)
        )

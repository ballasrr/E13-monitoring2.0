"""Запросы к базе по площадкам. Единственное место с SQL."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.station import Station


class StationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, station_id: int) -> Station | None:
        """Поиск по первичному ключу. session.get сначала смотрит
        в кэш текущей сессии и только потом идёт в базу."""
        return await self.session.get(Station, station_id)

    async def get_by_code(self, code: str) -> Station | None:
        stmt = select(Station).where(Station.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Station]:
        """Список площадок. limit и offset обязательны: без них
        на тысяче объектов ответ станет неподъёмным."""
        stmt = select(Station).order_by(Station.name).limit(limit).offset(offset)
        if not include_archived:
            stmt = stmt.where(Station.archived.is_(False))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, station: Station) -> Station:
        self.session.add(station)
        # flush отправляет INSERT в базу и возвращает присвоенный id,
        # но транзакцию не закрывает. commit делает сервис — он один
        # решает, когда работа закончена целиком.
        await self.session.flush()
        return station

    async def delete(self, station: Station) -> None:
        await self.session.delete(station)
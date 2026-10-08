"""Запросы к базе по оборудованию."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charger import Charger


class ChargerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, charger_id: int) -> Charger | None:
        return await self.session.get(Charger, charger_id)

    async def get_by_serial(self, serial: str) -> Charger | None:
        """Серийный номер — естественный ключ оборудования.
        По нему узнаём станцию при повторном импорте."""
        stmt = select(Charger).where(Charger.serial == serial)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_station(self, station_id: int) -> list[Charger]:
        stmt = (
            select(Charger)
            .where(Charger.station_id == station_id)
            .order_by(Charger.name, Charger.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, charger: Charger) -> Charger:
        self.session.add(charger)
        await self.session.flush()
        return charger

    async def delete(self, charger: Charger) -> None:
        await self.session.delete(charger)

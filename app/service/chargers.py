"""Бизнес-логика по оборудованию."""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.charger import Charger
from app.repositories.charger import ChargerRepository
from app.repositories.station import StationRepository
from app.schemas.charger import ChargerCreate, ChargerUpdate


class ChargerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ChargerRepository(session)
        self.stations = StationRepository(session)

    async def get(self, charger_id: int) -> Charger:
        charger = await self.repo.get(charger_id)
        if charger is None:
            raise NotFoundError("Оборудование не найдено")
        return charger

    async def list_by_station(self, station_id: int) -> list[Charger]:
        # Проверяем площадку, чтобы на несуществующий id отдать 404,
        # а не пустой список: пустой ответ выглядит как «станций нет».
        await self._ensure_station_exists(station_id)
        return await self.repo.list_by_station(station_id)

    async def create(self, station_id: int, payload: ChargerCreate) -> Charger:
        await self._ensure_station_exists(station_id)
        await self._ensure_serial_free(payload.serial)

        charger = Charger(station_id=station_id, **payload.model_dump())
        await self.repo.add(charger)
        await self.session.commit()
        return charger

    async def update(self, charger_id: int, payload: ChargerUpdate) -> Charger:
        charger = await self.get(charger_id)
        changes = payload.model_dump(exclude_unset=True)

        if "serial" in changes:
            await self._ensure_serial_free(changes["serial"], exclude_id=charger.id)

        for field, value in changes.items():
            setattr(charger, field, value)

        await self.session.commit()
        return charger

    async def mark_service(self, charger_id: int) -> Charger:
        """Отметка о проведённом ТО: сдвигает дату последнего обслуживания
        на сегодня, от неё считается следующий срок."""
        charger = await self.get(charger_id)
        charger.last_service_at = date.today()
        await self.session.commit()
        return charger

    async def delete(self, charger_id: int) -> None:
        """Оборудование удаляется насовсем — в отличие от площадки,
        у него нет архива: станцию либо демонтировали, либо нет."""
        charger = await self.get(charger_id)
        await self.repo.delete(charger)
        await self.session.commit()

    async def _ensure_station_exists(self, station_id: int) -> None:
        if await self.stations.get(station_id) is None:
            raise NotFoundError("Площадка не найдена")

    async def _ensure_serial_free(
        self, serial: str | None, exclude_id: int | None = None
    ) -> None:
        """Серийный номер уникален. Пустой пропускаем: у части
        оборудования его просто не записали."""
        if not serial:
            return
        existing = await self.repo.get_by_serial(serial)
        if existing is not None and existing.id != exclude_id:
            raise ConflictError(f"Серийный номер «{serial}» уже занят")

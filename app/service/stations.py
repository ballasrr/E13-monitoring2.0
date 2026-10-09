"""Бизнес-логика по площадкам."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.station import Station
from app.repositories.station import StationRepository
from app.schemas.station import StationCreate, StationUpdate


class StationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = StationRepository(session)

    async def get(self, station_id: int) -> Station:
        station = await self.repo.get(station_id)
        if station is None:
            raise NotFoundError("Площадка не найдена")
        return station

    async def list(
        self,
        *,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Station]:
        return await self.repo.list(
            include_archived=include_archived, limit=limit, offset=offset
        )

    async def count(self, *, include_archived: bool = False) -> int:
        return await self.repo.count(include_archived=include_archived)

    async def create(self, payload: StationCreate) -> Station:
        await self._ensure_code_free(payload.code)
        station = Station(**payload.model_dump())
        await self.repo.add(station)
        await self.session.commit()
        return station

    async def update(self, station_id: int, payload: StationUpdate) -> Station:
        station = await self.get(station_id)

        # exclude_unset=True — в словарь попадут только те поля, которые клиент
        # действительно прислал. Без него отсутствующие поля пришли бы как None
        # и затёрли данные в базе.
        changes = payload.model_dump(exclude_unset=True)

        if "code" in changes:
            await self._ensure_code_free(changes["code"], exclude_id=station.id)

        for field, value in changes.items():
            setattr(station, field, value)

        await self.session.commit()
        return station

    async def archive(self, station_id: int) -> Station:
        """Обратимое удаление: объект пропадает из списка, но остаётся в базе."""
        station = await self.get(station_id)
        station.archived = True
        await self.session.commit()
        return station

    async def _ensure_code_free(
        self, code: str | None, exclude_id: int | None = None
    ) -> None:
        """Код объекта должен быть уникальным. exclude_id нужен при изменении:
        площадка не конфликтует сама с собой."""
        if not code:
            return
        existing = await self.repo.get_by_code(code)
        if existing is not None and existing.id != exclude_id:
            raise ConflictError(f"Код «{code}» уже занят")
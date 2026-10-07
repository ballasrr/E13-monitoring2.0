"""Ручки по площадкам."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.station import StationCreate, StationOut, StationUpdate
from app.service.stations import StationService

router = APIRouter(prefix="/stations", tags=["Площадки"])


@router.get("", response_model=list[StationOut], summary="Список площадок")
async def list_stations(
    include_archived: bool = Query(False, description="Показывать архивные"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    return await StationService(session).list(
        include_archived=include_archived, limit=limit, offset=offset
    )


@router.post(
    "",
    response_model=StationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать площадку",
)
async def create_station(
    payload: StationCreate,
    session: AsyncSession = Depends(get_session),
):
    return await StationService(session).create(payload)


@router.get("/{station_id}", response_model=StationOut, summary="Карточка площадки")
async def get_station(
    station_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await StationService(session).get(station_id)


@router.patch("/{station_id}", response_model=StationOut, summary="Изменить площадку")
async def update_station(
    station_id: int,
    payload: StationUpdate,
    session: AsyncSession = Depends(get_session),
):
    return await StationService(session).update(station_id, payload)


@router.delete("/{station_id}", response_model=StationOut, summary="В архив")
async def archive_station(
    station_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await StationService(session).archive(station_id)
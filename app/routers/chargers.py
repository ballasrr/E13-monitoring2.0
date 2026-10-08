"""Ручки по оборудованию.

Список и создание живут под площадкой: оборудование без неё не существует.
Работа с конкретной станцией — по её собственному адресу.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.charger import ChargerCreate, ChargerOut, ChargerUpdate
from app.schemas.common import Message
from app.service.chargers import ChargerService

router = APIRouter(tags=["Оборудование"])


@router.get(
    "/stations/{station_id}/chargers",
    response_model=list[ChargerOut],
    summary="Оборудование площадки",
)
async def list_chargers(
    station_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await ChargerService(session).list_by_station(station_id)


@router.post(
    "/stations/{station_id}/chargers",
    response_model=ChargerOut,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить оборудование",
)
async def create_charger(
    station_id: int,
    payload: ChargerCreate,
    session: AsyncSession = Depends(get_session),
):
    return await ChargerService(session).create(station_id, payload)


@router.get("/chargers/{charger_id}", response_model=ChargerOut, summary="Карточка")
async def get_charger(
    charger_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await ChargerService(session).get(charger_id)


@router.patch("/chargers/{charger_id}", response_model=ChargerOut, summary="Изменить")
async def update_charger(
    charger_id: int,
    payload: ChargerUpdate,
    session: AsyncSession = Depends(get_session),
):
    return await ChargerService(session).update(charger_id, payload)


@router.post(
    "/chargers/{charger_id}/service",
    response_model=ChargerOut,
    summary="Отметить ТО",
)
async def mark_service(
    charger_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await ChargerService(session).mark_service(charger_id)


@router.delete("/chargers/{charger_id}", response_model=Message, summary="Удалить")
async def delete_charger(
    charger_id: int,
    session: AsyncSession = Depends(get_session),
):
    await ChargerService(session).delete(charger_id)
    return Message(message="Оборудование удалено")

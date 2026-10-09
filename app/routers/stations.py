"""Ручки по площадкам."""
from fastapi import APIRouter, Query, Response, status

from app.routers.deps import AdminUser, EditorUser, SessionDep, ViewerUser
from app.schemas.station import StationCreate, StationOut, StationUpdate
from app.service.stations import StationService

router = APIRouter(prefix="/stations", tags=["Площадки"])


@router.get(
    "",
    response_model=list[StationOut],
    summary="Список площадок",
    description=(
        "Срез по limit и offset. Общее число подходящих записей "
        "возвращается в заголовке **X-Total-Count** — по нему строится "
        "постраничная навигация."
    ),
)
async def list_stations(
    session: SessionDep,
    response: Response,
    _: ViewerUser,
    include_archived: bool = Query(False, description="Показывать архивные"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    service = StationService(session)
    # Счётчик отдаём заголовком, а не меняем форму ответа на
    # {"items": [...], "total": N}: тело остаётся обычным массивом,
    # и уже написанные клиенты не ломаются.
    response.headers["X-Total-Count"] = str(
        await service.count(include_archived=include_archived)
    )
    return await service.list(
        include_archived=include_archived, limit=limit, offset=offset
    )


@router.post(
    "",
    response_model=StationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать площадку",
)
async def create_station(
    payload: StationCreate, session: SessionDep, _: EditorUser
):
    return await StationService(session).create(payload)


@router.get("/{station_id}", response_model=StationOut, summary="Карточка площадки")
async def get_station(station_id: int, session: SessionDep, _: ViewerUser):
    return await StationService(session).get(station_id)


@router.patch("/{station_id}", response_model=StationOut, summary="Изменить площадку")
async def update_station(
    station_id: int, payload: StationUpdate, session: SessionDep, _: EditorUser
):
    return await StationService(session).update(station_id, payload)


@router.delete("/{station_id}", response_model=StationOut, summary="В архив")
async def archive_station(station_id: int, session: SessionDep, _: AdminUser):
    return await StationService(session).archive(station_id)

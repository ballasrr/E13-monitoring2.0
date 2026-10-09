"""Ручки выгрузки реестра.

Файлы отдаём через Response с заголовком Content-Disposition:
attachment — тогда в Swagger появляется ссылка «Download file»,
а браузер сохраняет файл, а не пытается его показать.
"""
from datetime import date

from fastapi import APIRouter, Response

from app.routers.deps import SessionDep, ViewerUser
from app.service.export import ExportService, render_csv

router = APIRouter(prefix="/export", tags=["Выгрузка"])

XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CSV_MEDIA = "text/csv; charset=utf-8"


def _file(data: bytes, name: str, media: str, ext: str) -> Response:
    # Дата в имени: пять выгрузок за неделю, и без неё в папке
    # «Загрузки» уже не разобраться, какая свежая.
    stamp = date.today().isoformat()
    return Response(
        content=data,
        media_type=media,
        headers={
            "Content-Disposition": f'attachment; filename="{name}-{stamp}.{ext}"'
        },
    )


@router.get(
    "/registry.xlsx",
    summary="Вся сеть одной книгой Excel",
    description=(
        "Три листа: «Площадки» со всеми характеристиками, "
        "«Оборудование» с привязкой к площадке и «Комплектность» — "
        "матрица документов. Шапка закреплена, включён автофильтр, "
        "отсутствующие и просроченные документы подсвечены красным."
    ),
)
async def registry_xlsx(session: SessionDep, _: ViewerUser) -> Response:
    data = await ExportService(session).workbook()
    return _file(data, "e13-registry", XLSX_MEDIA, "xlsx")


@router.get(
    "/stations.csv",
    summary="Реестр площадок в CSV",
    description=(
        "То же, что лист «Площадки», но отдельным CSV — для скриптов "
        "и сторонних систем. Для чтения человеком берите .xlsx: с CSV "
        "на Windows вечная морока с кодировкой."
    ),
)
async def stations_csv(session: SessionDep, _: ViewerUser) -> Response:
    table = await ExportService(session).stations_table()
    return _file(render_csv(table), "stations", CSV_MEDIA, "csv")


@router.get(
    "/chargers.csv",
    summary="Оборудование в CSV",
    description="Все зарядные станции сети с привязкой к площадке.",
)
async def chargers_csv(session: SessionDep, _: ViewerUser) -> Response:
    table = await ExportService(session).chargers_table()
    return _file(render_csv(table), "chargers", CSV_MEDIA, "csv")


@router.get(
    "/compliance.csv",
    summary="Матрица комплектности в CSV",
    description=(
        "Площадки по строкам, типы документов по столбцам. В клетке "
        "«НЕТ», дата окончания срока либо «есть» для бессрочных."
    ),
)
async def compliance_csv(session: SessionDep, _: ViewerUser) -> Response:
    table = await ExportService(session).compliance_table()
    return _file(render_csv(table), "compliance", CSV_MEDIA, "csv")


@router.get(
    "/stations.json",
    summary="Полная выгрузка в JSON",
    description=(
        "Площадки вместе с оборудованием и документами, все поля без "
        "отбора. Для переноса данных и разбора сторонними "
        "инструментами, а не для чтения человеком."
    ),
)
async def stations_json(session: SessionDep, _: ViewerUser) -> dict:
    return await ExportService(session).stations_json()

"""Ручки контроля комплектности и сроков."""
from dataclasses import asdict

from fastapi import APIRouter

from app.routers.deps import SessionDep, ViewerUser
from app.schemas.compliance import (
    AlertOut,
    AlertsSummary,
    ChecklistRowOut,
    StationComplianceOut,
)
from app.service.compliance import ComplianceService

router = APIRouter(prefix="/compliance", tags=["Контроль сроков"])


@router.get(
    "/config",
    summary="Правила комплектности и пороги",
    description=(
        "Единый источник правды для интерфейса: типы документов, "
        "обязательный набор по стадиям объекта и пороги предупреждений. "
        "Фронтенд берёт правила отсюда, а не хранит свою копию."
    ),
)
async def config(_: ViewerUser) -> dict:
    return ComplianceService.config()


@router.get(
    "/alerts",
    response_model=AlertsSummary,
    summary="Замечания по всей сети",
    description=(
        "Что требует внимания по всем площадкам сразу: отсутствующие "
        "документы, истекающие сроки, гарантия и ТО. Отсортировано "
        "по срочности."
    ),
)
async def network_alerts(session: SessionDep, _: ViewerUser):
    items = await ComplianceService(session).network()
    counts = {"overdue": 0, "warning": 0, "soon": 0}
    for alert in items:
        counts[alert.level] = counts.get(alert.level, 0) + 1
    return AlertsSummary(
        counts=counts,
        total=len(items),
        items=[AlertOut(**asdict(a)) for a in items],
    )


@router.get(
    "/stations/{station_id}",
    response_model=StationComplianceOut,
    summary="Комплектность площадки",
    description=(
        "Замечания по одному объекту плюс полная карта документов: "
        "по каждому типу видно, есть ли он, обязателен ли на текущей "
        "стадии и до какого числа действует."
    ),
)
async def station_compliance(station_id: int, session: SessionDep, _: ViewerUser):
    result = await ComplianceService(session).for_station(station_id)
    return StationComplianceOut(
        alerts=[AlertOut(**asdict(a)) for a in result.alerts],
        checklist=[ChecklistRowOut(**asdict(r)) for r in result.checklist],
    )

"""Контракты API для контроля сроков."""
from datetime import date

from pydantic import BaseModel


class AlertOut(BaseModel):
    """Одно замечание.

    Поля station_* продублированы внутри каждого замечания намеренно:
    в сводке по сети они приходят вперемешку, и клиенту не нужно
    ходить за названием площадки отдельным запросом.
    """

    kind: str
    level: str
    title: str
    detail: str = ""
    code: str | None = None
    due: date | None = None
    days: int | None = None
    document_id: int | None = None
    charger_id: int | None = None
    station_id: int | None = None
    station_code: str = ""
    station_name: str = ""


class ChecklistRowOut(BaseModel):
    code: str
    title: str
    expires: bool
    required: bool
    count: int
    document_id: int | None = None
    doc_number: str = ""
    valid_until: date | None = None
    days: int | None = None


class StationComplianceOut(BaseModel):
    alerts: list[AlertOut]
    checklist: list[ChecklistRowOut]


class AlertsSummary(BaseModel):
    counts: dict[str, int]
    total: int
    items: list[AlertOut]

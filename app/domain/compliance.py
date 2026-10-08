"""Правила контроля комплектности и сроков.

Чистая логика без базы и без HTTP: на вход — факты об объекте, на выходе —
список замечаний. Благодаря этому правила проверяются юнит-тестами
за миллисекунды, без поднятого Postgres.
"""
from calendar import monthrange
from dataclasses import dataclass, field
from datetime import date

from app.domain import documents as docs
from app.models.enums import ALERT_RANK, STATION_STATUS_RU, AlertKind, AlertLevel


# ── Входные факты ────────────────────────────────────────────────────────────
# Простые структуры вместо моделей SQLAlchemy: правила не должны знать,
# откуда взялись данные.
@dataclass(frozen=True, slots=True)
class DocumentFacts:
    id: int
    doc_type: str
    title: str = ""
    doc_number: str = ""
    valid_until: date | None = None


@dataclass(frozen=True, slots=True)
class ChargerFacts:
    id: int
    label: str
    status: str
    serial: str = ""
    installed_at: date | None = None
    warranty_until: date | None = None
    last_service_at: date | None = None
    service_interval_months: int | None = None


@dataclass(frozen=True, slots=True)
class StationFacts:
    id: int
    code: str
    name: str
    status: str
    documents: tuple[DocumentFacts, ...] = ()
    chargers: tuple[ChargerFacts, ...] = ()


# ── Результат ────────────────────────────────────────────────────────────────
@dataclass(slots=True)
class Alert:
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


@dataclass(slots=True)
class ChecklistRow:
    """Строка карты комплектности: по каждому типу документа — есть или нет."""

    code: str
    title: str
    expires: bool
    required: bool
    count: int
    document_id: int | None = None
    doc_number: str = ""
    valid_until: date | None = None
    days: int | None = None


@dataclass(slots=True)
class StationCompliance:
    alerts: list[Alert] = field(default_factory=list)
    checklist: list[ChecklistRow] = field(default_factory=list)


# ── Вспомогательное ──────────────────────────────────────────────────────────
def add_months(start: date, months: int) -> date:
    """Прибавляет месяцы, не выходя за границы месяца.

    31 января плюс месяц — это 28 или 29 февраля, а не «31 февраля».
    """
    total = start.month - 1 + int(months)
    year = start.year + total // 12
    month = total % 12 + 1
    return date(year, month, min(start.day, monthrange(year, month)[1]))


def level_for_days(days: int) -> str | None:
    """Насколько срочно. None — до срока ещё далеко, тревожить незачем."""
    if days < 0:
        return AlertLevel.OVERDUE
    if days <= docs.WARN_DAYS:
        return AlertLevel.WARNING
    if days <= docs.SOON_DAYS:
        return AlertLevel.SOON
    return None


def _sort_alerts(alerts: list[Alert]) -> list[Alert]:
    """Сначала самое срочное, внутри уровня — с наибольшей просрочкой."""
    return sorted(
        alerts,
        key=lambda a: (ALERT_RANK[a.level], a.days if a.days is not None else -10_000),
    )


# ── Основные правила ─────────────────────────────────────────────────────────
def evaluate_station(
    station: StationFacts, today: date | None = None
) -> StationCompliance:
    today = today or date.today()
    alerts: list[Alert] = []

    required = docs.required_for(station.status)
    strict = docs.is_strict(station.status)

    by_type: dict[str, list[DocumentFacts]] = {}
    for d in station.documents:
        by_type.setdefault(d.doc_type, []).append(d)

    # 1. Обязательные документы, которых нет
    for code in required:
        if code in by_type:
            continue
        alerts.append(
            Alert(
                kind=AlertKind.MISSING_DOC,
                # На пусконаладке и в работе отсутствие документа критично,
                # на ранних стадиях — просто предупреждение: работа ещё идёт.
                level=AlertLevel.OVERDUE if strict else AlertLevel.WARNING,
                title=f"Нет документа: {docs.doc_title(code)}",
                detail=(
                    "Объект на стадии «"
                    f"{STATION_STATUS_RU.get(station.status, station.status)}»"
                ),
                code=code,
            )
        )

    # 2. Документы с истекающим сроком действия
    for d in station.documents:
        if not d.valid_until:
            continue
        days = (d.valid_until - today).days
        level = level_for_days(days)
        if level is None:
            continue
        name = docs.doc_title(d.doc_type)
        detail = " ".join(
            part
            for part in (f"№ {d.doc_number}" if d.doc_number else "", d.title)
            if part
        ).strip()
        alerts.append(
            Alert(
                kind=AlertKind.DOC_EXPIRY,
                level=level,
                title=("Истёк срок: " if days < 0 else "Истекает срок: ") + name,
                detail=detail,
                code=d.doc_type,
                due=d.valid_until,
                days=days,
                document_id=d.id,
            )
        )

    # 3. Оборудование: гарантия и плановое ТО
    for c in station.chargers:
        # Ещё не установленную станцию обслуживать нечего
        if c.status == "planned":
            continue

        if c.warranty_until:
            days = (c.warranty_until - today).days
            level = level_for_days(days)
            if level is not None:
                alerts.append(
                    Alert(
                        kind=AlertKind.WARRANTY,
                        level=level,
                        title=(
                            "Гарантия истекла: "
                            if days < 0
                            else "Заканчивается гарантия: "
                        )
                        + c.label,
                        detail=f"S/N {c.serial}" if c.serial else "",
                        due=c.warranty_until,
                        days=days,
                        charger_id=c.id,
                    )
                )

        # Срок следующего ТО считаем от последнего обслуживания,
        # а пока его не было — от даты установки.
        base = c.last_service_at or c.installed_at
        if c.service_interval_months and base:
            due = add_months(base, c.service_interval_months)
            days = (due - today).days
            level = level_for_days(days)
            if level is not None:
                alerts.append(
                    Alert(
                        kind=AlertKind.SERVICE,
                        level=level,
                        title=("Просрочено ТО: " if days < 0 else "Подходит срок ТО: ")
                        + c.label,
                        detail=(
                            f"Последнее ТО {base.strftime('%d.%m.%Y')}, "
                            f"периодичность {c.service_interval_months} мес."
                        ),
                        due=due,
                        days=days,
                        charger_id=c.id,
                    )
                )

    # Проставляем площадку всем замечаниям разом — в сводке по сети
    # нужно понимать, к какому объекту относится каждое.
    for a in alerts:
        a.station_id = station.id
        a.station_code = station.code
        a.station_name = station.name

    return StationCompliance(
        alerts=_sort_alerts(alerts),
        checklist=build_checklist(station, today),
    )


def build_checklist(
    station: StationFacts, today: date | None = None
) -> list[ChecklistRow]:
    """Полная карта: по каждому типу документа — есть, обязателен, до когда."""
    today = today or date.today()
    required = set(docs.required_for(station.status))

    by_type: dict[str, list[DocumentFacts]] = {}
    for d in station.documents:
        by_type.setdefault(d.doc_type, []).append(d)

    rows: list[ChecklistRow] = []
    for dt in docs.DOC_TYPES:
        found = by_type.get(dt.code, [])
        best: DocumentFacts | None = None
        for d in found:
            # показываем тот документ, что действует дольше остальных
            if best is None or (d.valid_until or date.min) > (best.valid_until or date.min):
                best = d
        days = (best.valid_until - today).days if best and best.valid_until else None
        rows.append(
            ChecklistRow(
                code=dt.code,
                title=dt.title,
                expires=dt.expires,
                required=dt.code in required,
                count=len(found),
                document_id=best.id if best else None,
                doc_number=best.doc_number if best else "",
                valid_until=best.valid_until if best else None,
                days=days,
            )
        )
    return rows


def worst_level(alerts: list[Alert]) -> str | None:
    """Самое срочное из замечаний — им красится точка на карте."""
    if not alerts:
        return None
    return min((a.level for a in alerts), key=lambda level: ALERT_RANK[level])

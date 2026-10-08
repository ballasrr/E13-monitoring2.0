"""Мост между базой и правилами контроля.

Сервис достаёт объекты из репозитория, превращает их в простые факты
и отдаёт в domain.compliance, где живут сами правила. Так правила
остаются свободными от SQLAlchemy и проверяются тестами без базы.
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.domain import compliance as rules
from app.domain import documents as docs
from app.models.charger import Charger
from app.models.document import Document
from app.models.enums import ALERT_RANK
from app.models.station import Station
from app.repositories.station import StationRepository


def station_to_facts(
    station: Station, documents: list[Document], chargers: list[Charger]
) -> rules.StationFacts:
    return rules.StationFacts(
        id=station.id,
        code=station.code or "",
        name=station.name,
        status=station.status,
        documents=tuple(
            rules.DocumentFacts(
                id=d.id,
                doc_type=d.doc_type,
                # если название не заполнили, берём имя файла
                title=d.title or d.original_name,
                doc_number=d.doc_number or "",
                valid_until=d.valid_until,
            )
            for d in documents
            # считаем только актуальные редакции: прошлые уже не действуют
            if d.is_current
        ),
        chargers=tuple(
            rules.ChargerFacts(
                id=c.id,
                label=c.label,
                status=c.status,
                serial=c.serial or "",
                installed_at=c.installed_at,
                warranty_until=c.warranty_until,
                last_service_at=c.last_service_at,
                service_interval_months=c.service_interval_months,
            )
            for c in chargers
        ),
    )


class ComplianceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.stations = StationRepository(session)

    async def for_station(
        self, station_id: int, today: date | None = None
    ) -> rules.StationCompliance:
        station = await self.stations.get_full(station_id)
        if station is None:
            raise NotFoundError("Площадка не найдена")
        facts = station_to_facts(
            station, list(station.documents), list(station.chargers)
        )
        return rules.evaluate_station(facts, today)

    async def network(self, today: date | None = None) -> list[rules.Alert]:
        """Все замечания по сети, отсортированные по срочности."""
        alerts: list[rules.Alert] = []
        for station in await self.stations.list_with_relations():
            facts = station_to_facts(
                station, list(station.documents), list(station.chargers)
            )
            alerts.extend(rules.evaluate_station(facts, today).alerts)

        alerts.sort(
            key=lambda a: (
                ALERT_RANK[a.level],
                a.days if a.days is not None else -10_000,
                a.station_name,
            )
        )
        return alerts

    @staticmethod
    def config() -> dict:
        """Справочники и пороги для интерфейса — единый источник правды.

        Фронтенд берёт правила отсюда, а не хранит свою копию: иначе
        при изменении требований пришлось бы править в двух местах.
        """
        return {
            "doc_types": [
                {"code": d.code, "title": d.title, "expires": d.expires}
                for d in docs.DOC_TYPES
            ],
            "required_by_status": {
                str(status): list(codes)
                for status, codes in docs.REQUIRED_BY_STATUS.items()
            },
            "strict_statuses": sorted(str(s) for s in docs.STRICT_STATUSES),
            "warn_days": docs.WARN_DAYS,
            "soon_days": docs.SOON_DAYS,
            "default_service_months": docs.DEFAULT_SERVICE_MONTHS,
            "today": date.today().isoformat(),
        }

"""Справочник типов документов.

Чистые правила: ни базы, ни HTTP. Поэтому их можно проверять тестами
за миллисекунды и звать откуда угодно — хоть из скрипта импорта.
"""
from dataclasses import dataclass

from app.models.enums import StationStatus


@dataclass(frozen=True, slots=True)
class DocType:
    code: str
    title: str
    expires: bool  # есть ли у документа срок действия


DOC_TYPES: tuple[DocType, ...] = (
    DocType("land_lease", "Договор аренды земельного участка", True),
    DocType("tech_spec", "Технические условия на присоединение", True),
    DocType("tp_act", "Акт технологического присоединения", False),
    DocType("power_supply", "Договор электроснабжения", True),
    DocType("project", "Проектная документация", False),
    DocType("scheme", "Схемы и чертежи", False),
    DocType("commissioning_act", "Акт ввода в эксплуатацию", False),
    DocType("permit", "Разрешения и согласования", True),
    DocType("service_contract", "Договор на обслуживание", True),
    DocType("insurance", "Страховой полис", True),
    DocType("passport", "Паспорта оборудования", False),
    DocType("photo", "Фотографии и изображения", False),
    DocType("act", "Акты прочие", False),
    DocType("report", "Отчёты", False),
    DocType("other", "Прочее", False),
)

DOC_TYPE_BY_CODE: dict[str, DocType] = {d.code: d for d in DOC_TYPES}


def doc_title(code: str) -> str:
    """Человеческое название типа. Неизвестный код возвращаем как есть —
    лучше показать код, чем уронить ответ."""
    found = DOC_TYPE_BY_CODE.get(code)
    return found.title if found else code


def doc_expires(code: str) -> bool:
    found = DOC_TYPE_BY_CODE.get(code)
    return bool(found and found.expires)


def is_known_doc_type(code: str) -> bool:
    return code in DOC_TYPE_BY_CODE


# Какие документы обязаны быть на объекте в зависимости от его стадии.
# Единственное место, где это задано: интерфейс получает правила
# через /compliance/config, поэтому менять нужно только здесь.
REQUIRED_BY_STATUS: dict[str, tuple[str, ...]] = {
    StationStatus.PLANNED: ("land_lease",),
    StationStatus.DESIGN: ("land_lease", "tech_spec"),
    StationStatus.PERMITS: ("land_lease", "tech_spec", "project"),
    StationStatus.CONSTRUCTION: ("land_lease", "tech_spec", "project"),
    StationStatus.COMMISSIONING: ("land_lease", "tech_spec", "project", "tp_act"),
    StationStatus.OPERATING: (
        "land_lease", "tech_spec", "project", "tp_act",
        "power_supply", "commissioning_act", "photo",
    ),
    StationStatus.MAINTENANCE: (
        "land_lease", "tech_spec", "project", "tp_act",
        "power_supply", "commissioning_act", "photo",
    ),
    StationStatus.CLOSED: (),
}

# Стадии, на которых отсутствие обязательного документа критично, а не просто
# предупреждение: объект уже работает, значит бумаги должны быть на руках.
STRICT_STATUSES: frozenset[str] = frozenset(
    {StationStatus.COMMISSIONING, StationStatus.OPERATING, StationStatus.MAINTENANCE}
)


def required_for(status: str) -> tuple[str, ...]:
    return REQUIRED_BY_STATUS.get(status, ())


def is_strict(status: str) -> bool:
    return status in STRICT_STATUSES


# Пороги предупреждений о сроках, в днях
WARN_DAYS = 30   # «истекает совсем скоро» — жёлтый
SOON_DAYS = 90   # «на горизонте» — синий

DEFAULT_SERVICE_MONTHS = 12

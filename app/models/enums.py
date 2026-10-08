"""Перечисления предметной области.

В базе хранятся строками: так миграции проще, а список значений
можно расширять, не меняя тип колонки.
"""
from enum import StrEnum


class StationStatus(StrEnum):
    PLANNED = "planned"
    DESIGN = "design"
    PERMITS = "permits"
    CONSTRUCTION = "construction"
    COMMISSIONING = "commissioning"
    OPERATING = "operating"
    MAINTENANCE = "maintenance"
    CLOSED = "closed"


# Подписи для интерфейса. Держим рядом со значениями, чтобы при добавлении
# новой стадии не забыть про перевод.
STATION_STATUS_RU = {
    StationStatus.PLANNED: "Планируется",
    StationStatus.DESIGN: "Проектирование",
    StationStatus.PERMITS: "Согласования",
    StationStatus.CONSTRUCTION: "Строительство",
    StationStatus.COMMISSIONING: "Пусконаладка",
    StationStatus.OPERATING: "Работает",
    StationStatus.MAINTENANCE: "Обслуживание",
    StationStatus.CLOSED: "Закрыта",
}

class ChargerStatus(StrEnum):
    WORKING = "working"
    FAULT = "fault"
    MAINTENANCE = "maintenance"
    PLANNED = "planned"


CHARGER_STATUS_RU = {
    ChargerStatus.WORKING: "Работает",
    ChargerStatus.FAULT: "Неисправна",
    ChargerStatus.MAINTENANCE: "На ТО",
    ChargerStatus.PLANNED: "Планируется",
}

class Role(StrEnum):
    VIEWER = "viewer"      # смотрит карту и карточки, скачивает документы
    EDITOR = "editor"      # правит данные, добавляет объекты, грузит файлы
    ADMIN = "admin"        # плюс пользователи, архив и удаление


# Роли упорядочены: доступ даётся, если уровень не ниже требуемого.
# Словарь, а не сравнение строк — иначе "admin" < "viewer" по алфавиту.
ROLE_LEVEL = {Role.VIEWER: 0, Role.EDITOR: 1, Role.ADMIN: 2}

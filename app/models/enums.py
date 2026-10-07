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
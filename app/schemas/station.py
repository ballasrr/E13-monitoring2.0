"""Контракты API для площадок."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StationStatus


class StationBase(BaseModel):
    """Поля, общие для создания и ответа."""

    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    status: StationStatus = StationStatus.PLANNED

    # ge и le — проверка диапазона. Координаты за пределами Земли
    # отсекаются сразу, до похода в базу.
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: str = Field(default="", max_length=500)


class StationCreate(StationBase):
    """Тело запроса на создание."""


class StationUpdate(BaseModel):
    """Тело запроса на изменение.

    Все поля необязательные: клиент присылает только то, что меняет.
    Поэтому наследоваться от StationBase нельзя — там name обязателен.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    status: StationStatus | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)


class StationOut(StationBase):
    """Ответ API."""

    # Позволяет собрать схему прямо из объекта SQLAlchemy,
    # а не только из словаря.
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived: bool
    created_at: datetime
    updated_at: datetime
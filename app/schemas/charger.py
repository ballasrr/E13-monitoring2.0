"""Контракты API для оборудования."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ChargerStatus


class ChargerBase(BaseModel):
    """Поля, общие для создания и ответа."""

    name: str = Field(default="", max_length=255)
    vendor: str = Field(default="", max_length=160)
    model: str = Field(default="", max_length=160)
    serial: str = Field(default="", max_length=128)
    ocpp_id: str = Field(default="", max_length=128)

    power_kw: float | None = Field(default=None, ge=0, le=10000)
    current_type: str = Field(default="DC", max_length=8)
    connectors: str = Field(default="", max_length=255)
    connector_count: int | None = Field(default=None, ge=0, le=64)
    tariff_rub: float | None = Field(default=None, ge=0)

    status: ChargerStatus = ChargerStatus.WORKING

    installed_at: date | None = None
    warranty_until: date | None = None
    last_service_at: date | None = None
    service_interval_months: int | None = Field(default=None, ge=1, le=120)

    notes: str = ""


class ChargerCreate(ChargerBase):
    """Тело запроса на создание.

    station_id здесь нет: площадка берётся из адреса,
    POST /stations/{station_id}/chargers.
    """


class ChargerUpdate(BaseModel):
    """Тело запроса на изменение: только изменяемые поля."""

    name: str | None = Field(default=None, max_length=255)
    vendor: str | None = Field(default=None, max_length=160)
    model: str | None = Field(default=None, max_length=160)
    serial: str | None = Field(default=None, max_length=128)
    ocpp_id: str | None = Field(default=None, max_length=128)

    power_kw: float | None = Field(default=None, ge=0, le=10000)
    current_type: str | None = Field(default=None, max_length=8)
    connectors: str | None = Field(default=None, max_length=255)
    connector_count: int | None = Field(default=None, ge=0, le=64)
    tariff_rub: float | None = Field(default=None, ge=0)

    status: ChargerStatus | None = None

    installed_at: date | None = None
    warranty_until: date | None = None
    last_service_at: date | None = None
    service_interval_months: int | None = Field(default=None, ge=1, le=120)

    notes: str | None = None


class ChargerOut(ChargerBase):
    """Ответ API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int
    created_at: datetime
    updated_at: datetime

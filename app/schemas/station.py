"""Контракты API для площадок."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StationStatus


class StationBase(BaseModel):
    """Поля, общие для создания и ответа.

    Обязательных всего три: название и координаты. Остальное
    заполняется по мере того, как объект проходит стадии.
    """

    name: str = Field(min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    status: StationStatus = StationStatus.PLANNED

    # ── География ────────────────────────────────────────────────────────
    # ge и le — проверка диапазона. Координаты за пределами Земли
    # отсекаются сразу, до похода в базу.
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    address: str = Field(default="", max_length=500)
    region: str = Field(default="", max_length=160)
    site_type: str = Field(default="", max_length=160)

    # ── Земля и права ────────────────────────────────────────────────────
    land_status: str = Field(default="", max_length=160)
    landlord: str = Field(default="", max_length=255)
    opened_at: date | None = None

    # ── Электрика и присоединение ────────────────────────────────────────
    grid_company: str = Field(default="", max_length=255)
    tp_number: str = Field(default="", max_length=64)
    transformer_kva: float | None = Field(default=None, ge=0)
    allocated_kw: float | None = Field(default=None, ge=0)
    voltage: str = Field(default="", max_length=64)
    connection_contract: str = Field(default="", max_length=128)
    connection_date: date | None = None
    meter_number: str = Field(default="", max_length=128)
    energy_supplier: str = Field(default="", max_length=255)

    # ── Инфраструктура ───────────────────────────────────────────────────
    has_canopy: bool = False
    has_lighting: bool = False
    has_cctv: bool = False
    has_internet: bool = False
    internet_type: str = Field(default="", max_length=128)
    has_fence: bool = False
    has_wc: bool = False
    has_cafe: bool = False
    has_signage: bool = False
    accessible: bool = False
    parking_spots: int | None = Field(default=None, ge=0, le=1000)
    surface_type: str = Field(default="", max_length=128)

    # ── Персонал и режим работы ──────────────────────────────────────────
    has_operator: bool = False
    staff_count: int | None = Field(default=None, ge=0, le=1000)
    work_schedule: str = Field(default="", max_length=128)
    responsible_name: str = Field(default="", max_length=160)
    responsible_phone: str = Field(default="", max_length=64)
    service_company: str = Field(default="", max_length=255)

    notes: str = ""
    custom: dict = Field(default_factory=dict)


class StationCreate(StationBase):
    """Тело запроса на создание."""


class StationUpdate(BaseModel):
    """Тело запроса на изменение.

    Все поля необязательные: клиент присылает только то, что меняет.
    Поэтому наследоваться от StationBase нельзя — там name и координаты
    обязательны.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, max_length=64)
    status: StationStatus | None = None

    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=500)
    region: str | None = Field(default=None, max_length=160)
    site_type: str | None = Field(default=None, max_length=160)

    land_status: str | None = Field(default=None, max_length=160)
    landlord: str | None = Field(default=None, max_length=255)
    opened_at: date | None = None

    grid_company: str | None = Field(default=None, max_length=255)
    tp_number: str | None = Field(default=None, max_length=64)
    transformer_kva: float | None = Field(default=None, ge=0)
    allocated_kw: float | None = Field(default=None, ge=0)
    voltage: str | None = Field(default=None, max_length=64)
    connection_contract: str | None = Field(default=None, max_length=128)
    connection_date: date | None = None
    meter_number: str | None = Field(default=None, max_length=128)
    energy_supplier: str | None = Field(default=None, max_length=255)

    has_canopy: bool | None = None
    has_lighting: bool | None = None
    has_cctv: bool | None = None
    has_internet: bool | None = None
    internet_type: str | None = Field(default=None, max_length=128)
    has_fence: bool | None = None
    has_wc: bool | None = None
    has_cafe: bool | None = None
    has_signage: bool | None = None
    accessible: bool | None = None
    parking_spots: int | None = Field(default=None, ge=0, le=1000)
    surface_type: str | None = Field(default=None, max_length=128)

    has_operator: bool | None = None
    staff_count: int | None = Field(default=None, ge=0, le=1000)
    work_schedule: str | None = Field(default=None, max_length=128)
    responsible_name: str | None = Field(default=None, max_length=160)
    responsible_phone: str | None = Field(default=None, max_length=64)
    service_company: str | None = Field(default=None, max_length=255)

    notes: str | None = None
    custom: dict | None = None


class StationOut(StationBase):
    """Ответ API."""

    # Позволяет собрать схему прямо из объекта SQLAlchemy,
    # а не только из словаря.
    model_config = ConfigDict(from_attributes=True)

    id: int
    archived: bool
    created_at: datetime
    updated_at: datetime

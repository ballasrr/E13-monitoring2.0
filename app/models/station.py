"""Площадка: адрес, на котором стоит одна или несколько зарядных станций."""
from datetime import date

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import StationStatus


class Station(Base, TimestampMixin):
    __tablename__ = "stations"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Код объекта — человеческий идентификатор вроде ASKO-01.
    # index=True, потому что по нему будут искать.
    code: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(24), default=StationStatus.PLANNED, nullable=False, index=True
    )

    # ── География ────────────────────────────────────────────────────────
    # Numeric, а не float: у float есть погрешность округления,
    # а координаты должны храниться точно.
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    region: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    site_type: Mapped[str] = mapped_column(String(160), default="", nullable=False)

    # ── Земля и права ────────────────────────────────────────────────────
    land_status: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    landlord: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    opened_at: Mapped[date | None] = mapped_column(Date)

    # ── Электрика и присоединение ────────────────────────────────────────
    grid_company: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    tp_number: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    transformer_kva: Mapped[float | None] = mapped_column(Numeric(10, 2))
    allocated_kw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    voltage: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    connection_contract: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    connection_date: Mapped[date | None] = mapped_column(Date)
    meter_number: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    energy_supplier: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    # ── Инфраструктура площадки ──────────────────────────────────────────
    has_canopy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_lighting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_cctv: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_internet: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    internet_type: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    has_fence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_wc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_cafe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_signage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accessible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parking_spots: Mapped[int | None] = mapped_column(Integer)
    surface_type: Mapped[str] = mapped_column(String(128), default="", nullable=False)

    # ── Персонал и режим работы ──────────────────────────────────────────
    has_operator: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    staff_count: Mapped[int | None] = mapped_column(Integer)
    work_schedule: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    responsible_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    responsible_phone: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    service_company: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Запасной карман для полей, которых мы не предусмотрели. Добавить
    # сюда значение можно без миграции — но и искать по нему медленнее,
    # поэтому всё частое должно становиться нормальной колонкой.
    custom: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    # Архив — обратимое удаление: объект пропадает с карты, но остаётся в базе.
    archived: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # Оборудование на площадке. Колонок в таблице stations не добавляет:
    # внешний ключ лежит в chargers.station_id.
    chargers = relationship(
        "Charger", back_populates="station", cascade="all, delete-orphan", lazy="raise"
    )

    def __repr__(self) -> str:
        return f"<Station {self.code or self.id} {self.name}>"

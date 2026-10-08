"""Зарядная станция — конкретное оборудование на площадке."""
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ChargerStatus


class Charger(Base, TimestampMixin):
    __tablename__ = "chargers"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ondelete="CASCADE" — удалили площадку, её оборудование ушло следом.
    # Правило живёт в самой базе, а не только в Python.
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    vendor: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    model: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    serial: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)

    # Идентификатор в системе оператора OCPP — по нему потом подтянем
    # реальный статус и загрузку станции.
    ocpp_id: Mapped[str] = mapped_column(String(128), default="", nullable=False, index=True)

    power_kw: Mapped[float | None] = mapped_column(Numeric(10, 2))
    current_type: Mapped[str] = mapped_column(String(8), default="DC", nullable=False)
    connectors: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    connector_count: Mapped[int | None] = mapped_column(Integer)
    tariff_rub: Mapped[float | None] = mapped_column(Numeric(10, 2))

    status: Mapped[str] = mapped_column(
        String(24), default=ChargerStatus.WORKING, nullable=False, index=True
    )

    # ── Гарантия и обслуживание ──────────────────────────────────────────
    installed_at: Mapped[date | None] = mapped_column(Date)
    warranty_until: Mapped[date | None] = mapped_column(Date)
    last_service_at: Mapped[date | None] = mapped_column(Date)
    service_interval_months: Mapped[int | None] = mapped_column(Integer)

    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # lazy="raise" — обращение к charger.station без явной загрузки
    # поднимет ошибку вместо тихого похода в базу.
    station = relationship("Station", back_populates="chargers", lazy="raise")

    @property
    def label(self) -> str:
        """Как называть станцию в предупреждениях и журнале."""
        return (
            self.name
            or " ".join(x for x in (self.vendor, self.model) if x)
            or "Зарядная станция"
        )

    def __repr__(self) -> str:
        return f"<Charger {self.id} {self.name or self.serial}>"

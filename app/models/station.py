"""Площадка: адрес, на котором стоит одна или несколько зарядных станций."""
from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

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

    # Numeric, а не float: у float есть погрешность округления,
    # а координаты должны храниться точно.
    lat: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(Numeric(10, 7), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)

    # Архив — обратимое удаление: объект пропадает с карты, но остаётся в базе.
    archived: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Station {self.code or self.id} {self.name}>"
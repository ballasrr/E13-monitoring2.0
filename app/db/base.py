"""Базовый класс для всех таблиц."""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """От него наследуются все модели. SQLAlchemy по нему собирает схему."""


class TimestampMixin:
    """Когда строка создана и когда менялась.

    Значения проставляет сама база (func.now()), а не Python — так время
    одинаковое независимо от того, с какой машины пришёл запрос.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
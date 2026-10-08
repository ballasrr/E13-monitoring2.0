"""Учётная запись."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.models.enums import Role


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Сам пароль не хранится нигде и никогда — только его хеш.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    role: Mapped[str] = mapped_column(String(16), default=Role.VIEWER, nullable=False)

    # Отключённая запись остаётся в базе: её нельзя удалить, пока на неё
    # ссылаются загруженные документы и записи журнала.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Номер поколения выданных токенов. Он зашит в каждый токен, и при
    # проверке сравнивается с этим значением. Выход увеличивает номер —
    # все ранее выданные токены разом перестают подходить.
    token_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    def __repr__(self) -> str:
        return f"<User {self.login} ({self.role})>"

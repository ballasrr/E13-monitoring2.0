"""Неудачные попытки входа.

Хранятся в базе, а не в памяти процесса. Причина простая: на сервере
приложение работает в нескольких рабочих процессах, и у каждого был бы
свой счётчик — лимит в двадцать попыток превращался бы в восемьдесят.
Плюс память обнуляется при каждом перезапуске, а перезапуск может
устроить и сам подбирающий, если найдёт способ уронить процесс.

Таблица намеренно простая: строка на попытку, старые чистятся при
проверке. Отдельное хранилище вроде Redis здесь было бы лишней
движущейся частью — записей мало, и живут они минуты.
"""
from datetime import datetime

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    __table_args__ = (
        # Запросы всегда вида «попытки с этого адреса за последние N минут»,
        # поэтому индекс составной и именно в таком порядке.
        Index("ix_login_attempts_ip_time", "ip", "attempted_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # 45 символов — максимальная длина адреса IPv6 в текстовом виде.
    ip: Mapped[str] = mapped_column(String(45), nullable=False)
    # Логин сохраняем, чтобы по журналу было видно, что именно перебирали:
    # один логин или список. Для самого ограничителя он не нужен.
    login: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

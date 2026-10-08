"""Вход, учётные записи, защита от перебора."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TooManyRequestsError,
)
from app.core.security import create_session_token, hash_password, verify_password
from app.models.enums import Role
from app.models.user import User
from app.repositories.user import UserRepository

# Счётчик неудачных попыток входа по адресу. Живёт в памяти процесса:
# для одного сервера этого хватает, а переживать перезапуск ему незачем.
_attempts: dict[str, list[datetime]] = {}


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = UserRepository(session)

    # ── Вход ─────────────────────────────────────────────────────────────
    async def authenticate(
        self, login: str, password: str, ip: str
    ) -> tuple[User, str]:
        self._check_rate_limit(ip)

        user = await self.repo.get_by_login(login)
        if user is None or not verify_password(password, user.password_hash):
            self._register_failure(ip)
            # Один и тот же текст на «нет такого логина» и «неверный пароль»:
            # иначе по ответу можно узнать, какие логины существуют.
            raise AuthenticationError("Неверный логин или пароль")

        if not user.is_active:
            raise AuthenticationError("Учётная запись отключена")

        user.last_login_at = datetime.now(timezone.utc)
        await self.session.commit()
        _attempts.pop(ip, None)

        return user, create_session_token(user.id, user.token_version)

    async def logout(self, user: User) -> None:
        """Настоящий выход: все выданные этому человеку токены становятся
        недействительны сразу, на всех устройствах."""
        user.token_version += 1
        await self.session.commit()

    async def get_active_user(self, user_id: int) -> User | None:
        user = await self.repo.get(user_id)
        return user if user is not None and user.is_active else None

    # ── Создание учётной записи ──────────────────────────────────────────
    async def create_user(
        self, login: str, password: str, full_name: str, role: Role
    ) -> User:
        if await self.repo.get_by_login(login) is not None:
            raise ConflictError(f"Логин «{login}» уже занят")

        user = User(
            login=login,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
        )
        await self.repo.add(user)
        await self.session.commit()
        return user

    async def ensure_first_admin(self) -> User | None:
        """Создаёт администратора при первом запуске.

        Только если пользователей нет вообще: иначе каждый перезапуск
        воскрешал бы удалённую учётку с паролем из настроек.
        """
        if await self.repo.count() > 0:
            return None
        return await self.create_user(
            settings.first_admin_login,
            settings.first_admin_password,
            settings.first_admin_name,
            Role.ADMIN,
        )

    # ── Защита от перебора ───────────────────────────────────────────────
    def _check_rate_limit(self, ip: str) -> None:
        window = timedelta(minutes=settings.login_attempts_window_minutes)
        now = datetime.now(timezone.utc)
        recent = [t for t in _attempts.get(ip, []) if now - t < window]
        _attempts[ip] = recent
        if len(recent) >= settings.login_attempts_limit:
            raise TooManyRequestsError(
                "Слишком много неудачных попыток входа. Подождите несколько минут."
            )

    def _register_failure(self, ip: str) -> None:
        _attempts.setdefault(ip, []).append(datetime.now(timezone.utc))

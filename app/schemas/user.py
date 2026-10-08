"""Контракты API для учётных записей."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Role


class TokenOut(BaseModel):
    """Ответ на вход.

    Первые два поля требует стандарт OAuth2 — по ним Swagger понимает,
    что получил токен. Остальные добавлены для фронтенда, чтобы он сразу
    знал, кто вошёл, и не делал второй запрос.
    """

    access_token: str
    token_type: str = "bearer"
    login: str
    full_name: str
    role: Role


class UserOut(BaseModel):
    """Ответ API. Хеша пароля здесь нет и быть не должно."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    full_name: str
    role: Role
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

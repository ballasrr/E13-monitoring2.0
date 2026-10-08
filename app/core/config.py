from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Приложение ───────────────────────────────────────────────────────
    app_name: str = "E13 Monitoring API"
    debug: bool = False

    # Все ручки живут под /api/v1. Если контракт придётся менять
    # несовместимо, рядом появится /api/v2, а первая версия продолжит
    # работать, пока фронтенд не перейдёт.
    api_prefix: str = "/api/v1"

    # ── База данных ──────────────────────────────────────────────────────
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str = "e13_monitoring"
    postgres_user: str = "e13"
    postgres_password: str = "e13"

    db_echo: bool = False

    # ── Сессии и безопасность ────────────────────────────────────────────
    # Ключ подписи сессионных токенов. Сменить его — значит разлогинить всех.
    # Сгенерировать: python -c "import secrets; print(secrets.token_hex(48))"
    secret_key: str = Field(default="change-me-in-production", min_length=8)
    session_cookie: str = "e13sid"
    session_days: int = 30

    # true включать только после HTTPS: иначе браузер не примет cookie
    # и войти станет невозможно.
    secure_cookie: bool = False

    # Защита от перебора паролей
    login_attempts_limit: int = 20
    login_attempts_window_minutes: int = 10

    # ── Первый администратор (создаётся при старте, если таблица пуста) ──
    first_admin_login: str = "admin"
    first_admin_password: str = "admin12345"
    first_admin_name: str = "Администратор"

    @property
    def database_url(self) -> str:
        """Строка подключения для asyncpg. Понадобится на следующем шаге."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Настройки читаются один раз, дальше берутся из кэша."""
    return Settings()


settings = get_settings()
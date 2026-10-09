from functools import lru_cache
from pathlib import Path

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

    # Откуда фронтенду разрешено обращаться к API. Браузер отправит
    # запрос с заголовком Origin, и если его нет в этом списке, ответ
    # до JavaScript не дойдёт — это защита самого браузера, а не наша.
    # В .env пишется строкой через запятую:
    #   CORS_ORIGINS=http://localhost:5173,https://e13.example.ru
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ── База данных ──────────────────────────────────────────────────────
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_db: str = "e13_monitoring"
    postgres_user: str = "e13"
    postgres_password: str = "e13"

    db_echo: bool = False

    # ── Сессии и безопасность ────────────────────────────────────────────
    # Ключ подписи токенов. Сменить его — значит разлогинить всех.
    # Сгенерировать: python -c "import secrets; print(secrets.token_hex(48))"
    secret_key: str = Field(default="change-me-in-production", min_length=8)
    session_days: int = 30

    # Защита от перебора паролей
    login_attempts_limit: int = 20
    login_attempts_window_minutes: int = 10

    # ── Файлы ────────────────────────────────────────────────────────────
    # Папка внутри контейнера, к которой примонтирован том Docker
    storage_dir: Path = Path("/data/uploads")
    max_upload_mb: int = 100

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    # ── Первый администратор (создаётся при старте, если таблица пуста) ──
    first_admin_login: str = "admin"
    first_admin_password: str = "admin12345"
    first_admin_name: str = "Администратор"

    @property
    def cors_origin_list(self) -> list[str]:
        """Строка из .env превращается в список.

        Звёздочку разрешаем только в отладке: с ней API открыт любому
        сайту, и чужая страница сможет дёргать его в браузере человека,
        который у нас залогинен.
        """
        items = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if "*" in items and not self.debug:
            raise ValueError(
                "CORS_ORIGINS=* запрещён вне отладки — перечислите адреса явно"
            )
        return items

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
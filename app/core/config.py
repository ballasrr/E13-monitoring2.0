from functools import lru_cache

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
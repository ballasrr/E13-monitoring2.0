"""Подключение к базе: движок и фабрика сессий."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Движок один на всё приложение: внутри него пул соединений.
engine = create_async_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_pre_ping=True,  # проверяет соединение перед выдачей: лечит обрывы
)

# Фабрика сессий. expire_on_commit=False — чтобы после commit можно было
# читать поля объекта без похода в базу.
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость FastAPI: даёт сессию на один запрос и закрывает после.

    Используется так:
        async def handler(session: AsyncSession = Depends(get_session)):
    """
    async with SessionFactory() as session:
        yield session
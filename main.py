"""Точка входа: здесь собирается приложение FastAPI."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import SessionFactory
from app.routers import auth, chargers, compliance, documents, stations
from app.service.auth import AuthService

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("e13")

ART = """\

⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⠤⣄⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣀⠴⠚⠉⠁⠀⠀⠀⠀⠀⠈⠉⠳⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣠⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⣆⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⡞⡥⠀⠀⠀⠀⣠⠴⢀⣠⠤⢦⡀⠀⠀⠀⠀⠀⠈⣆⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢠⡞⢸⠁⠀⠀⣠⢚⡥⠚⠉⠀⠀⠘⣗⡄⠀⠀⢰⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢾⠇⡎⠀⠀⣰⡳⠋⠀⠀⣠⣤⠶⠢⡿⣸⣆⠀⠈⣧⣄⢸⠁⠀⠀⠀⠀⠀⠀
⠀⠀⢸⡄⢳⣠⣾⡟⠓⠆⠀⠘⠙⢀⣤⣶⢿⣤⣹⡅⠀⣿⠈⣿⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⡇⠸⡇⣾⡛⣶⡦⠀⠀⠀⠛⢱⢼⣷⠸⠋⢣⠀⡇⣹⠛⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢱⠀⠹⣏⠉⢟⣻⣀⠀⠀⠀⠐⠛⠛⠐⠀⠘⣴⡽⣇⠀⢸⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⢇⠀⠘⡄⠀⠀⢸⡁⠀⠀⠀⠀⠀⠀⠀⠀⣿⢀⢹⡀⠈⣧⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠈⢦⠀⢻⢦⡀⠈⠰⠶⠒⠂⠀⠀⢀⡤⠀⡇⢘⡆⢇⠀⠸⣷⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠳⡼⡀⣟⡶⢄⡀⠀⢀⡠⠖⠁⠀⢀⡇⢸⢻⠸⡀⠀⣿⢇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⠏⢳⠟⢀⠷⠈⣹⡇⠀⠀⠀⠀⣼⢣⡞⢸⠀⡇⢰⣼⢸⠀⠀⠀
⠀⠀⠀⠀⠀⢀⠎⣠⠋⢀⡼⠟⠊⠟⠀⠀⠀⠀⠀⣿⠀⠑⢯⣀⣇⣎⢏⡞⠀⠀⠀
⠀⠀⠀⢀⡠⠾⠔⠓⢞⣁⣀⣀⠀⠀⠀⠀⠀⠀⠀⢻⣀⣀⣀⡈⠛⠿⠯⣀⠀⠀⠀
⠀⠀⢠⠋⠀⠀⠀⠀⠀⠀⠀⠀⠉⠁⠐⠉⠉⠉⠉⠉⣧⡀⠀⠀⠀⠀⠀⠀⠑⡄⠀
⠀⠀⢻⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠧⠀⠀⠀⠀⠀⠀⠀⢹⡆
⠀⠀⢸⠀⠀⡼⠁⠀⠐⢆⡀⠀⠀⠀⠀⠀⣀⠄⠂⠀⠀⠀⣤⠀⠀⠀⠀⠀⠀⡼⠃
⠀⠀⠘⡤⠊⠀⠀⠀⠀⠀⠈⠣⠀⠀⢰⠃⠀⠀⠀⠀⠀⠀⠹⡀⠀⠀⠀⠀⢠⠇⠀
⠀⣠⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⢐⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⠀⠀⡎⠀⠀
⢠⢇⣠⡂⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠘⡄⠀⠀⡸⠀⠀⠀
⢸⡀⠛⠆⢀⠀⠀⠀⠀⠀⠀⠀⣸⠀⠀⠀⠀⠀⠀⠀⢓⠷⠀⠀⡇⠀⢀⠇⠀⠀⠀
⠀⢷⡀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠸⡀⠀⠀⠀⠀⠀⠂⠀⠀⠀⣰⠁⠀⣾⠀⠀⠀⠀
⠀⠀⠑⢤⣀⠀⠀⢀⣠⠴⠋⠀⠀⠙⢦⡀⠀⠀⠀⠀⠀⣀⡴⠁⠀⢠⠃⠀⠀⠀⠀
⠀⠀⠀⠀⢠⢻⠉⠁⠀⠀⠀⠀⠀⠀⠀⠈⠉⠒⠒⠒⠉⡽⠀⠀⠀⡼⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠸⣾⠀⠐⠀⠀⠀⠀⠀⠑⢤⡀⠀⠀⠀⠀⠀⡇⠀⠀⢠⠇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣿⡄⠀⠀⢠⡀⠀⠀⠀⠀⠙⣄⠀⠀⠀⢰⠁⠀⠀⣼⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢿⣇⠀⠀⢸⠀⠀⠀⠀⠀⠀⠈⠁⠀⢀⡜⠀⠀⠀⡗⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢸⢸⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⢠⡇⠀⠀⠀⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠸⣿⡆⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠐⡇⠀⠀⢰⠃⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣻⠁⠀⠸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢣⠀⠀⡞⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢠⠃⠀⠀⠸⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠳⡼⠁⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⢠⠏⠀⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⡎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢦⡀⠀⠀⠀⠀
    
"""

# Тройные кавычки сохраняют переносы строк, а ``` оборачивает картинку
# в блок кода: Swagger рисует описание как Markdown и без этого схлопнул бы
# пробелы и перенёс строки — рисунок бы поехал.
DESCRIPTION = f"Реестр электрозарядных станций\n\n```\n{ART}\n```"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Выполняется один раз при старте приложения."""
    async with SessionFactory() as session:
        created = await AuthService(session).ensure_first_admin()
    if created:
        logger.warning(
            "Создан первый администратор «%s». Смените пароль сразу после входа.",
            created.login,
        )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=DESCRIPTION,
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Превращает доменные ошибки в HTTP-ответы одной формы.
    Фронтенд всегда читает поле «error», что бы ни случилось."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Последний рубеж: любая непредусмотренная ошибка пишется в лог
    с полным следом, а клиенту уходит короткий ответ той же формы,
    что и остальные. Подробности наружу не отдаём — в них бывают пути
    и куски запросов."""
    logger.exception("Необработанная ошибка на %s", request.url.path)
    return JSONResponse(
        status_code=500, content={"error": "Внутренняя ошибка сервера"}
    )


@app.get("/api/health", tags=["Служебное"], summary="Проверка живости")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(stations.router, prefix=settings.api_prefix)
app.include_router(chargers.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(compliance.router, prefix=settings.api_prefix)

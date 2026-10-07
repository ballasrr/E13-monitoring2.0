from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import AppError
from app.routers import stations

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Реестр электрозарядных станций",
)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """Превращает доменные ошибки в HTTP-ответы одной формы.
    Фронтенд всегда читает поле «error», что бы ни случилось."""
    return JSONResponse(status_code=exc.status_code, content={"error": exc.message})


@app.get("/api/health", tags=["Служебное"], summary="Проверка живости")
async def health() -> dict:
    return {"status": "ok", "version": app.version}


app.include_router(stations.router, prefix=settings.api_prefix)
from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Реестр электрозарядных станций",
)

@app.get("/api/health", tags=["Служебное"], summary="Проверка живости")
async def health() -> dict:
    return {"status": "ok", "version": app.version}
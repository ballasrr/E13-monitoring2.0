from fastapi import FastAPI

app = FastAPI(title="EVMap API")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
FROM python:3.12-slim

# uv берём готовым бинарником из официального образа — быстрее, чем ставить pip-ом
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Зависимости — отдельным слоем: пока pyproject.toml и uv.lock не менялись,
# этот шаг берётся из кэша и не пересобирается при каждой правке кода.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Чтобы python и uvicorn брались из созданного окружения
ENV PATH="/app/.venv/bin:$PATH"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
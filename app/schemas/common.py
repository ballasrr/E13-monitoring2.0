"""Схемы, общие для всего API."""
from pydantic import BaseModel


class Message(BaseModel):
    """Простой текстовый ответ — когда возвращать нечего."""

    message: str

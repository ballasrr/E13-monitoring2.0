"""Контракты API для документов."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.documents import doc_title


class DocumentUpdate(BaseModel):
    """Правка карточки. Сам файл при этом не меняется —
    для нового файла загружается новая редакция."""

    doc_type: str | None = Field(default=None, max_length=48)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    doc_number: str | None = Field(default=None, max_length=128)
    doc_date: date | None = None
    valid_until: date | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    station_id: int

    doc_type: str
    doc_type_title: str = ""
    title: str
    description: str
    doc_number: str
    doc_date: date | None
    valid_until: date | None

    original_name: str
    mime: str
    size_bytes: int

    series_id: int
    version: int
    is_current: bool

    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, document) -> "DocumentOut":
        """Собирает ответ и подставляет человеческое название типа.

        Название не хранится в базе: справочник живёт в коде, и если
        переименовать тип, все старые документы покажут новое название.
        """
        out = cls.model_validate(document)
        out.doc_type_title = doc_title(document.doc_type)
        return out


class DocTypeOut(BaseModel):
    """Элемент справочника типов — фронтенду для выпадающего списка."""

    code: str
    title: str
    expires: bool

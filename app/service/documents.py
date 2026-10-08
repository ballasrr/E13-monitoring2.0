"""Бизнес-логика по документам: загрузка, версии, удаление."""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.storage import FileStorage, get_storage
from app.domain.documents import is_known_doc_type
from app.models.document import Document
from app.models.user import User
from app.repositories.document import DocumentRepository
from app.repositories.station import StationRepository


class DocumentService:
    def __init__(self, session: AsyncSession, storage: FileStorage | None = None) -> None:
        self.session = session
        self.repo = DocumentRepository(session)
        self.stations = StationRepository(session)
        # Хранилище передаётся снаружи — так в тестах можно подставить
        # поддельное и не трогать диск.
        self.storage = storage or get_storage()

    async def get(self, document_id: int) -> Document:
        document = await self.repo.get(document_id)
        if document is None:
            raise NotFoundError("Документ не найден")
        return document

    async def list_current(self, station_id: int) -> list[Document]:
        await self._ensure_station_exists(station_id)
        return await self.repo.list_current(station_id)

    async def versions(self, document_id: int) -> list[Document]:
        document = await self.get(document_id)
        return await self.repo.list_series(document.series_id)

    async def upload(
        self,
        station_id: int,
        *,
        content: bytes,
        filename: str,
        content_type: str,
        meta: dict,
        author: User,
    ) -> Document:
        """Сохраняет файл и заводит карточку.

        Если документ такого типа у площадки уже есть, новая запись
        становится его следующей редакцией: старая остаётся в истории
        вместе со своим файлом.
        """
        await self._ensure_station_exists(station_id)

        doc_type = meta.get("doc_type") or "other"
        if not is_known_doc_type(doc_type):
            raise ValidationError(f"Неизвестный тип документа: «{doc_type}»")

        previous = await self.repo.find_current(station_id, doc_type)

        stored = self.storage.save(content, filename)

        document = Document(
            station_id=station_id,
            doc_type=doc_type,
            title=meta.get("title") or "",
            description=meta.get("description") or "",
            doc_number=meta.get("doc_number") or "",
            doc_date=meta.get("doc_date"),
            valid_until=meta.get("valid_until"),
            original_name=filename,
            stored_name=stored.stored_name,
            mime=content_type,
            size_bytes=stored.size_bytes,
            checksum=stored.checksum,
            uploaded_by_id=author.id,
        )

        if previous is not None:
            # Продолжаем серию: номер серии наследуем, версию увеличиваем,
            # прежнюю редакцию снимаем с «актуальной».
            document.series_id = previous.series_id
            document.version = previous.version + 1
            document.supersedes_id = previous.id
            previous.is_current = False

        await self.repo.add(document)
        await self.session.commit()
        return document

    async def update_meta(self, document_id: int, changes: dict) -> Document:
        document = await self.get(document_id)
        doc_type = changes.get("doc_type")
        if doc_type is not None and not is_known_doc_type(doc_type):
            raise ValidationError(f"Неизвестный тип документа: «{doc_type}»")

        for field, value in changes.items():
            setattr(document, field, value)

        await self.session.commit()
        return document

    async def make_current(self, document_id: int) -> Document:
        """Возврат к прошлой редакции: делает её актуальной, не удаляя новую."""
        document = await self.get(document_id)
        for sibling in await self.repo.list_series(document.series_id):
            sibling.is_current = sibling.id == document.id
        await self.session.commit()
        return document

    async def delete(self, document_id: int) -> None:
        """Удаляет редакцию вместе с файлом.

        Если удалили актуальную, актуальной становится предыдущая —
        иначе документ исчез бы из карточки, хотя история осталась.
        """
        document = await self.get(document_id)
        stored_name = document.stored_name
        was_current = document.is_current
        series_id = document.series_id

        await self.repo.delete(document)
        await self.session.flush()

        if was_current:
            rest = await self.repo.list_series(series_id)
            if rest:
                rest[0].is_current = True

        await self.session.commit()
        # Файл удаляем после коммита: если транзакция откатится,
        # файл на диске останется — это лучше, чем карточка без файла.
        self.storage.delete(stored_name)

    def file_path(self, document: Document) -> Path:
        if not self.storage.exists(document.stored_name):
            raise NotFoundError("Файл документа не найден в хранилище")
        return self.storage.path(document.stored_name)

    async def _ensure_station_exists(self, station_id: int) -> None:
        if await self.stations.get(station_id) is None:
            raise NotFoundError("Площадка не найдена")

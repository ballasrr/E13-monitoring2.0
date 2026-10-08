"""Запросы к базе по документам."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, document_id: int) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list_current(self, station_id: int) -> list[Document]:
        """Только актуальные редакции — то, что видно в карточке площадки."""
        stmt = (
            select(Document)
            .where(Document.station_id == station_id, Document.is_current.is_(True))
            .order_by(Document.doc_type, Document.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_series(self, series_id: int) -> list[Document]:
        """Все редакции одного документа — история."""
        stmt = (
            select(Document)
            .where(Document.series_id == series_id)
            .order_by(Document.version.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_current(self, station_id: int, doc_type: str) -> Document | None:
        """Действующая редакция документа такого типа у площадки.
        Нужна, чтобы новая загрузка стала её продолжением, а не дублем."""
        stmt = select(Document).where(
            Document.station_id == station_id,
            Document.doc_type == doc_type,
            Document.is_current.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def add(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        return document

    async def delete(self, document: Document) -> None:
        await self.session.delete(document)

"""Документ или фотография, привязанные к площадке."""
from datetime import date

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Отдельная последовательность для номера серии: первая редакция документа
# получает новый номер, все последующие наследуют его.
document_series_seq = Sequence("document_series_seq", metadata=Base.metadata)


class Document(Base, TimestampMixin):
    """Повторная загрузка документа того же типа не затирает прежний файл.

    Все редакции одного документа связаны общим series_id; актуальная
    помечена is_current, предыдущие остаются в истории вместе со своими
    файлами, номерами и сроками.
    """

    __tablename__ = "documents"
    __table_args__ = (
        # Составные индексы под два самых частых запроса:
        # «документы такого типа у этой площадки» и «актуальная редакция серии»
        Index("ix_documents_station_type", "station_id", "doc_type"),
        Index("ix_documents_series_current", "series_id", "is_current"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(
        ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Что за документ ──────────────────────────────────────────────────
    doc_type: Mapped[str] = mapped_column(String(48), default="other", nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    doc_number: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    doc_date: Mapped[date | None] = mapped_column(Date)

    # По этому полю считаются просрочки и предупреждения
    valid_until: Mapped[date | None] = mapped_column(Date)

    # ── Файл на диске ────────────────────────────────────────────────────
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    # Имя в хранилище. unique — два документа не могут указывать на один файл.
    stored_name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    mime: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), default="", nullable=False)

    # ── Версии ───────────────────────────────────────────────────────────
    series_id: Mapped[int] = mapped_column(
        BigInteger,
        document_series_seq,
        server_default=document_series_seq.next_value(),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL")
    )

    # SET NULL, а не CASCADE: удалили пользователя — документ остаётся,
    # просто перестаёт быть подписан автором.
    uploaded_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    station = relationship("Station", back_populates="documents", lazy="raise")

    def __repr__(self) -> str:
        return f"<Document {self.id} {self.doc_type} v{self.version}>"

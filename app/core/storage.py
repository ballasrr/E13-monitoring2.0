"""Хранилище файлов.

Отдельный слой: сейчас файлы лежат на диске в томе Docker, но весь
остальной код обращается только к этому интерфейсу. Переезд на S3
сведётся к новой реализации FileStorage — сервисы и роутеры не изменятся.
"""
import hashlib
import re
import secrets
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class StoredFile:
    stored_name: str
    size_bytes: int
    checksum: str


class FileStorage(Protocol):
    """Контракт хранилища. Реализаций может быть несколько."""

    def save(self, data: bytes, original_name: str) -> StoredFile: ...
    def path(self, stored_name: str) -> Path: ...
    def delete(self, stored_name: str) -> None: ...
    def exists(self, stored_name: str) -> bool: ...


def safe_extension(filename: str) -> str:
    """Чистое расширение без сюрпризов.

    Из имени берём только суффикс, обрезаем до 12 символов и выкидываем
    всё, кроме букв, цифр и точки. Иначе кто-нибудь загрузит файл
    с именем «../../etc/passwd».
    """
    ext = Path(filename).suffix[:12]
    return re.sub(r"[^A-Za-z0-9.]", "", ext).lower()


class LocalFileStorage:
    """Файлы на диске. В контейнере это том, примонтированный в /data/uploads."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root or settings.storage_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, original_name: str) -> StoredFile:
        # Имя на диске случайное: кириллица и пробелы в путь не попадают,
        # одинаковые имена не затирают друг друга. Настоящее имя лежит
        # в базе и подставляется при скачивании.
        stored_name = secrets.token_hex(16) + safe_extension(original_name)
        (self.root / stored_name).write_bytes(data)
        return StoredFile(
            stored_name=stored_name,
            size_bytes=len(data),
            # Контрольная сумма — чтобы потом можно было проверить,
            # что файл на диске не побился и не подменён.
            checksum=hashlib.sha256(data).hexdigest(),
        )

    def path(self, stored_name: str) -> Path:
        candidate = (self.root / stored_name).resolve()
        # Защита от выхода за пределы папки загрузок
        if not str(candidate).startswith(str(self.root.resolve())):
            raise ValueError("Некорректное имя файла")
        return candidate

    def exists(self, stored_name: str) -> bool:
        try:
            return self.path(stored_name).is_file()
        except ValueError:
            return False

    def delete(self, stored_name: str) -> None:
        with suppress(ValueError):
            self.path(stored_name).unlink(missing_ok=True)


def get_storage() -> FileStorage:
    return LocalFileStorage()

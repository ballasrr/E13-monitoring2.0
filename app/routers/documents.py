"""Ручки по документам: загрузка, скачивание, версии."""
from datetime import date
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.errors import PayloadTooLargeError
from app.domain.documents import DOC_TYPES
from app.routers.deps import AdminUser, EditorUser, SessionDep, ViewerUser
from app.schemas.common import Message
from app.schemas.document import DocTypeOut, DocumentOut, DocumentUpdate
from app.service.documents import DocumentService

router = APIRouter(tags=["Документы"])


@router.get(
    "/doc-types",
    response_model=list[DocTypeOut],
    summary="Справочник типов документов",
    description="Фронтенд строит по нему выпадающий список при загрузке.",
)
async def doc_types(_: ViewerUser):
    return [DocTypeOut(code=d.code, title=d.title, expires=d.expires) for d in DOC_TYPES]


@router.get(
    "/stations/{station_id}/documents",
    response_model=list[DocumentOut],
    summary="Документы площадки",
    description="Только актуальные редакции. История — в /documents/{id}/versions.",
)
async def list_documents(station_id: int, session: SessionDep, _: ViewerUser):
    documents = await DocumentService(session).list_current(station_id)
    return [DocumentOut.from_model(d) for d in documents]


@router.post(
    "/stations/{station_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ",
    description=(
        "Если документ такого типа у площадки уже есть, новый файл станет "
        "его следующей редакцией, а прежняя сохранится в истории вместе "
        "со своим файлом."
    ),
)
async def upload_document(
    station_id: int,
    session: SessionDep,
    user: EditorUser,
    file: Annotated[UploadFile, File(description="Файл документа")],
    doc_type: Annotated[str, Form(description="Код из /doc-types")] = "other",
    valid_until: Annotated[
        str, Form(description="Действует до, ГГГГ-ММ-ДД. По нему считаются просрочки")
    ] = "",
):
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise PayloadTooLargeError(f"Файл больше {settings.max_upload_mb} МБ")

    document = await DocumentService(session).upload(
        station_id,
        content=content,
        filename=file.filename or "file",
        content_type=file.content_type or "application/octet-stream",
        # Номер, даты и срок действия заполняются потом, через
        # PATCH /documents/{id} — при загрузке они не нужны.
        meta={
            "doc_type": doc_type,
            "valid_until": date.fromisoformat(valid_until) if valid_until else None,
        },
        author=user,
    )
    return DocumentOut.from_model(document)


@router.get("/documents/{document_id}", response_model=DocumentOut, summary="Карточка")
async def get_document(document_id: int, session: SessionDep, _: ViewerUser):
    return DocumentOut.from_model(await DocumentService(session).get(document_id))


@router.get(
    "/documents/{document_id}/versions",
    response_model=list[DocumentOut],
    summary="Все редакции документа",
)
async def document_versions(document_id: int, session: SessionDep, _: ViewerUser):
    versions = await DocumentService(session).versions(document_id)
    return [DocumentOut.from_model(d) for d in versions]


@router.get(
    "/documents/{document_id}/content",
    summary="Скачать или открыть файл",
    response_class=FileResponse,
)
async def document_content(
    document_id: int,
    session: SessionDep,
    _: ViewerUser,
    download: bool = Query(False, description="Отдать файл как вложение"),
):
    service = DocumentService(session)
    document = await service.get(document_id)
    path = service.file_path(document)

    headers = {}
    if download:
        # filename*=UTF-8'' — иначе кириллица в имени файла превратится
        # в кракозябры: обычный filename допускает только латиницу.
        headers["Content-Disposition"] = (
            f"attachment; filename*=UTF-8''{quote(document.original_name)}"
        )
    return FileResponse(
        path,
        media_type=document.mime or "application/octet-stream",
        headers=headers,
    )


@router.patch(
    "/documents/{document_id}", response_model=DocumentOut, summary="Изменить карточку"
)
async def update_document(
    document_id: int, payload: DocumentUpdate, session: SessionDep, _: EditorUser
):
    document = await DocumentService(session).update_meta(
        document_id, payload.model_dump(exclude_unset=True)
    )
    return DocumentOut.from_model(document)


@router.post(
    "/documents/{document_id}/make-current",
    response_model=DocumentOut,
    summary="Сделать редакцию актуальной",
    description="Возврат к прошлой версии документа. Новая при этом не удаляется.",
)
async def make_current(document_id: int, session: SessionDep, _: EditorUser):
    document = await DocumentService(session).make_current(document_id)
    return DocumentOut.from_model(document)


@router.delete(
    "/documents/{document_id}", response_model=Message, summary="Удалить редакцию"
)
async def delete_document(document_id: int, session: SessionDep, _: AdminUser):
    await DocumentService(session).delete(document_id)
    return Message(message="Документ удалён")

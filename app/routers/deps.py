"""Зависимости FastAPI: сессия базы, текущий пользователь, проверка ролей.

Живут в слое роутеров: они знают про HTTP (заголовки, запрос),
а сервисы и репозитории — нет.
"""
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import AuthenticationError, PermissionError_
from app.core.security import read_session_token
from app.db.session import get_session
from app.models.enums import ROLE_LEVEL, Role
from app.models.user import User
from app.service.auth import AuthService

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Схема для Swagger: благодаря ей появляется кнопка Authorize с полями
# логина и пароля, а у защищённых ручек — замки.
# auto_error=False — ошибку поднимаем мы сами, своим текстом.
bearer_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


async def get_current_user(
    session: SessionDep,
    token: Annotated[str | None, Depends(bearer_scheme)] = None,
) -> User:
    # Единственный способ предъявить сессию — заголовок Authorization.
    # Так и Swagger, и фронтенд работают одинаково, и нет ситуации,
    # когда один способ сброшен, а другой продолжает давать доступ.
    if not token:
        raise AuthenticationError()

    parsed = read_session_token(token)
    if parsed is None:
        raise AuthenticationError("Сессия истекла, войдите заново")

    user_id, token_version = parsed
    user = await AuthService(session).get_active_user(user_id)
    if user is None:
        raise AuthenticationError("Учётная запись отключена")

    # Версия в токене должна совпадать с текущей. После выхода она
    # уже другая — значит, токен предъявили после logout.
    if token_version != user.token_version:
        raise AuthenticationError("Сессия завершена, войдите заново")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(minimum: Role):
    """Пускает дальше, только если роль пользователя не ниже требуемой."""

    async def dependency(user: CurrentUser) -> User:
        if ROLE_LEVEL[Role(user.role)] < ROLE_LEVEL[minimum]:
            raise PermissionError_()
        return user

    return dependency


ViewerUser = Annotated[User, Depends(require_role(Role.VIEWER))]
EditorUser = Annotated[User, Depends(require_role(Role.EDITOR))]
AdminUser = Annotated[User, Depends(require_role(Role.ADMIN))]


def client_ip(request: Request) -> str:
    """IP клиента с учётом того, что перед приложением стоит обратный прокси.

    Берём ПОСЛЕДНЕЕ значение из X-Forwarded-For, а не первое.

    Заголовок устроен как цепочка: каждый прокси дописывает в конец
    адрес того, от кого получил запрос. Начало цепочки приходит от
    клиента и подделывается тривиально — достаточно послать запрос
    со своим X-Forwarded-For, и первым в списке окажется выдуманный
    адрес. Подставляя каждый раз новый, можно подбирать пароль
    бесконечно, несмотря на ограничитель попыток.

    Последнее значение дописал наш собственный прокси (Caddy), и
    подделать его клиент не может: что бы он ни прислал, настоящий
    адрес всё равно окажется правее.

    Условие: прокси у нас ровно один. Если появится второй (CDN перед
    Caddy), отступать нужно будет на две позиции, иначе мы начнём
    считать адресом клиента адрес собственного CDN.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        hops = [part.strip() for part in forwarded.split(",") if part.strip()]
        if hops:
            return hops[-settings.trusted_proxy_hops]
    return request.client.host if request.client else "unknown"


ClientIP = Annotated[str, Depends(client_ip)]

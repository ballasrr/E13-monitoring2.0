"""Смена пароля администратора.

Эндпоинта смены пароля в API намеренно нет: пользователь один, и лишняя
ручка, через которую можно перехватить управление, системе не нужна.
Поэтому пароль меняется отсюда — с машины, где и так есть доступ к базе.

Запуск внутри контейнера:

    docker compose exec api python scripts/set_password.py admin
    docker compose -f docker-compose.prod.yml exec api python scripts/set_password.py admin

Пароль вводится скрыто и в истории команд не остаётся. Нового пароля
скрипт не печатает: сохраните его в менеджере паролей сразу.
"""
import asyncio
import getpass
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionFactory
from app.models.user import User


async def main(login: str) -> int:
    password = getpass.getpass(f"Новый пароль для «{login}»: ")
    if len(password) < 12:
        print("Слишком короткий пароль: нужно хотя бы 12 символов.", file=sys.stderr)
        return 1
    if password != getpass.getpass("Повторите: "):
        print("Пароли не совпали.", file=sys.stderr)
        return 1

    async with SessionFactory() as session:
        user = (
            await session.execute(select(User).where(User.login == login))
        ).scalar_one_or_none()

        if user is None:
            print(f"Пользователь «{login}» не найден.", file=sys.stderr)
            return 1

        user.password_hash = hash_password(password)
        # Поднимаем версию токена: все ранее выданные токены перестают
        # работать. Если пароль меняют из-за того, что он утёк, старая
        # сессия не должна пережить смену.
        user.token_version += 1
        await session.commit()

    print(f"Пароль для «{login}» изменён. Все текущие сессии завершены.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python scripts/set_password.py ЛОГИН", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(asyncio.run(main(sys.argv[1])))

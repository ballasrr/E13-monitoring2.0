"""Пароли и сессионные токены.

Эти функции — единственное, что отделяет чужого человека от всей базы,
поэтому проверяем не только «работает», но и «не работает, когда не
должно»: подделанная подпись, истёкший срок, мусор вместо токена.
"""
import base64
import json
import time

from app.core import security


# ── Пароли ───────────────────────────────────────────────────────────────────
def test_пароль_проверяется():
    stored = security.hash_password("asko2026")
    assert security.verify_password("asko2026", stored) is True


def test_неверный_пароль_не_проходит():
    stored = security.hash_password("asko2026")
    assert security.verify_password("asko2027", stored) is False
    assert security.verify_password("", stored) is False


def test_одинаковые_пароли_дают_разные_хеши():
    """У каждого пароля своя соль. Иначе по совпадению хешей было бы
    видно, что у двух людей одинаковый пароль, и один подобранный
    пароль вскрывал бы сразу все совпадающие."""
    assert security.hash_password("one") != security.hash_password("one")


def test_в_хеше_не_видно_самого_пароля():
    stored = security.hash_password("asko2026")
    assert "asko2026" not in stored


def test_хеш_помнит_число_итераций():
    """Число записано в самом хеше, поэтому его можно поднять позже,
    не ломая уже сохранённые пароли."""
    stored = security.hash_password("x")
    algo, rounds, salt, dk = stored.split("$")
    assert algo == "pbkdf2_sha256"
    assert int(rounds) == security.PBKDF2_ROUNDS


def test_испорченный_хеш_не_валит_приложение():
    for junk in ["", "мусор", "a$b$c", "pbkdf2_sha256$нечисло$aa$bb", None]:
        assert security.verify_password("x", junk) is False


# ── Токены ───────────────────────────────────────────────────────────────────
def test_токен_читается_обратно():
    token = security.create_session_token(user_id=7, token_version=3)
    assert security.read_session_token(token) == (7, 3)


def test_подделанный_токен_отвергается():
    """Меняем полезную нагрузку, не трогая подпись — она не сойдётся."""
    token = security.create_session_token(user_id=1, token_version=0)
    body, signature = token.split(".")

    payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    payload["uid"] = 999  # пытаемся стать другим пользователем
    forged_body = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )

    assert security.read_session_token(f"{forged_body}.{signature}") is None


def test_чужая_подпись_не_подходит():
    token = security.create_session_token(user_id=1)
    body, _ = token.split(".")
    assert security.read_session_token(f"{body}.чужаяподпись") is None


def test_истёкший_токен_отвергается(monkeypatch):
    token = security.create_session_token(user_id=1)

    # Настоящее время запоминаем заранее: security.time — это тот же
    # объект модуля time, что и у нас, поэтому лямбда, вызывающая
    # time.time() внутри себя, ушла бы в бесконечную рекурсию.
    later = time.time() + 400 * 86400   # токен живёт 30 дней
    monkeypatch.setattr(security.time, "time", lambda: later)

    assert security.read_session_token(token) is None


def test_мусор_вместо_токена():
    for junk in ["", "абв", "a.b.c", "....", "no-dot-at-all"]:
        assert security.read_session_token(junk) is None


def test_версия_токена_сохраняется():
    """По ней выход гасит все ранее выданные токены: сервер увеличивает
    версию у пользователя, и старые перестают сходиться."""
    assert security.read_session_token(security.create_session_token(1, 0))[1] == 0
    assert security.read_session_token(security.create_session_token(1, 5))[1] == 5

"""Пароли и подпись сессионных cookie.

Хеш пароля — PBKDF2-HMAC-SHA256 из стандартной библиотеки: без внешних
зависимостей и без сюрпризов совместимости, которые бывают у passlib с bcrypt.

Сессия — подписанный HMAC токен. Состояние на сервере не хранится: всё,
что нужно, лежит в самом токене, а подпись не даёт его подделать.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

from app.core.config import settings

# 200 000 итераций — столько, чтобы перебор был дорогим, но вход
# оставался быстрым. Число записывается в сам хеш, поэтому его можно
# поднять позже, не ломая старые пароли.
PBKDF2_ROUNDS = 200_000
_ALGO = "pbkdf2_sha256"


# ── Пароли ───────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    """Соль у каждого пароля своя: одинаковые пароли дают разные хеши."""
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{_ALGO}${PBKDF2_ROUNDS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_hex, dk_hex = stored.split("$")
        if algo != _ALGO:
            return False
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
        )
        # compare_digest сравнивает за одинаковое время независимо от того,
        # где строки разошлись: иначе по задержке можно подбирать хеш посимвольно.
        return hmac.compare_digest(dk.hex(), dk_hex)
    except (ValueError, AttributeError):
        return False


# ── Сессионные токены ────────────────────────────────────────────────────────
def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def create_session_token(user_id: int) -> str:
    payload = json.dumps(
        {"uid": user_id, "exp": int(time.time()) + settings.session_days * 86400}
    ).encode()
    body = _b64e(payload)
    signature = _b64e(
        hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    )
    return f"{body}.{signature}"


def read_session_token(token: str) -> int | None:
    """Возвращает id пользователя или None, если токен подделан или истёк."""
    try:
        body, signature = token.split(".")
        expected = _b64e(
            hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_b64d(body))
        if data.get("exp", 0) < time.time():
            return None
        return int(data["uid"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None

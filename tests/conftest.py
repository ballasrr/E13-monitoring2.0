"""Общие настройки для тестов.

Секретный ключ задаём до импорта приложения: иначе настройки прочитают
боевой .env, и тесты станут зависеть от окружения конкретной машины.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("DEBUG", "true")

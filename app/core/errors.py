"""Ошибки предметной области."""


class AppError(Exception):
    """Общий предок. Код ответа и текст заданы в потомках."""

    status_code = 400
    message = "Ошибка запроса"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class ValidationError(AppError):
    status_code = 422
    message = "Данные не прошли проверку"


class NotFoundError(AppError):
    status_code = 404
    message = "Объект не найден"


class ConflictError(AppError):
    status_code = 409
    message = "Конфликт данных"

class AuthenticationError(AppError):
    status_code = 401
    message = "Требуется вход в систему"


class PermissionError_(AppError):
    """С подчёркиванием: PermissionError — встроенное имя Python."""

    status_code = 403
    message = "Недостаточно прав"


class TooManyRequestsError(AppError):
    status_code = 429
    message = "Слишком много попыток, повторите позже"


class PayloadTooLargeError(AppError):
    status_code = 413
    message = "Файл слишком большой"

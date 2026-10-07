"""Ошибки предметной области."""


class AppError(Exception):
    """Общий предок. Код ответа и текст заданы в потомках."""

    status_code = 400
    message = "Ошибка запроса"

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    message = "Объект не найден"


class ConflictError(AppError):
    status_code = 409
    message = "Конфликт данных"
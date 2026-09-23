"""Ошибки API. В сообщениях никогда нет пользовательских данных."""


class ApiError(Exception):
    """Ошибка с машинным кодом, HTTP-статусом и сообщением по-русски."""

    def __init__(self, code: str, status: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.message = message

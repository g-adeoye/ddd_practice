class DomainError(Exception):
    pass


class UnknownAccount(DomainError):
    def __init__(self, account_id: int) -> None:
        super().__init__(f"unknown account ID: {account_id}")
        self.account_id = account_id


class InvalidAmount(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)

class BackPressureError(Exception):
    "Queue depth exceeded the high watermark."
    pass
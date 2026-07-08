from typing import Protocol
from ..domain.models import Job, Transaction, RiskResult


class BeneficiaryHistoryRepository(Protocol):
    def has_used_beneficiary_before(self, account_id: int, iban: str) -> bool: ...

    def account_exists(self, account_id: int) -> bool: ...


class CrossAccountIbanLookup(Protocol):
    def is_iban_shared_across_accounts(
        self, account_id: str, beneficiary_iban: str
    ) -> bool: ...


class ActivityRepository(Protocol):
    def get_amount_threshold_for_account(self, account_id: str) -> float: ...


class JobRepository(Protocol):
    def write_job(self, job: Job) -> None: ...

    def write_jobs(self, jobs: list[Job]) -> None: ...


class JobQueue(Protocol):
    def get_unprocessed_jobs(self) -> None: ...


class RiskScorerInterface(Protocol):
    def evaluate(self, transaction: Transaction) -> RiskResult: ...


class LoggerPort(Protocol):
    def info(self, message: str):
        pass

    def error(self, message: str):
        pass

    def warning(self, message: str):
        pass

    def critical(self, message: str):
        pass

    def exception(self, message: str):
        pass

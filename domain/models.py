from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID
from datetime import datetime


@dataclass(frozen=True)
class Transaction:
    amount: int
    account: int
    beneficiary_iban: str


@dataclass
class RiskResult:
    transaction: Transaction
    exceeded_threshold: bool
    new_beneficiary: bool

    @property
    def flagged(self) -> bool:
        return self.exceeded_threshold or self.new_beneficiary


@dataclass(frozen=True)
class Invoice:
    invoice_id: int
    issuing_account_id: str
    beneficiary_iban: str
    amount: int


@dataclass
class FraudRiskResult:
    invoice: Invoice
    shared_iban: bool
    amount_inconsistent: bool

    @property
    def flagged(self) -> bool:
        return self.shared_iban or self.amount_inconsistent


class JobState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"


@dataclass
class Job:
    id: UUID
    status: JobState
    priority: JobPriority
    payload: Transaction
    result: dict
    max_retries: int
    created_at: datetime
    updated_at: datetime | None

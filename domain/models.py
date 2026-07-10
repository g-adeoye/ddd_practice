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

    @staticmethod
    def from_str(label: str):
        label_class = {
            "PENDING": JobState.PENDING,
            "RUNNING": JobState.RUNNING,
            "COMPLETED": JobState.COMPLETED,
            "FAILED": JobState.FAILED,
        }
        class_ = label_class[label]

        if class_ is None:
            raise ValueError(f"Unknown status: {label}")

        return class_


class JobPriority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"

    @staticmethod
    def from_str(label: str):
        label_class = {
            "CRITICAL": JobPriority.CRITICAL,
            "HIGH": JobPriority.HIGH,
            "NORMAL": JobPriority.NORMAL,
        }
        class_ = label_class[label]

        if class_ is None:
            raise ValueError(f"Unknown priority: {label}")

        return class_


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

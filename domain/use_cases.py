from .models import Transaction, RiskResult, Invoice, FraudRiskResult
from ..ports.ports import (
    BeneficiaryHistoryRepository,
    CrossAccountIbanLookup,
    ActivityRepository,
)
from .errors import UnknownAccount, InvalidAmount


class RiskScorer:
    def __init__(
        self,
        transaction_threshold: int,
        beneficiary_history: BeneficiaryHistoryRepository,
    ):
        self.transaction_threshold = transaction_threshold
        self.beneficiary_history = beneficiary_history

    def evaluate(
        self,
        transaction: Transaction,
    ) -> RiskResult:
        if not self.beneficiary_history.account_exists(transaction.account):
            raise UnknownAccount(transaction.account)

        if transaction.amount <= 0:
            raise InvalidAmount("invalid transaction amount")

        exceeded_threshold = self.transaction_threshold < transaction.amount
        new_beneficiary = not self.beneficiary_history.has_used_beneficiary_before(
            transaction.account, transaction.beneficiary_iban
        )

        return RiskResult(
            transaction=transaction,
            exceeded_threshold=exceeded_threshold,
            new_beneficiary=new_beneficiary,
        )


class InvoiceFraudDetector:
    def __init__(
        self,
        accounts_repo: CrossAccountIbanLookup,
        activity_cost_ranges: ActivityRepository,
    ) -> None:
        self.accounts_repo = accounts_repo
        self.activity_cost_ranges = activity_cost_ranges

    def evaluate(self, invoice: Invoice) -> FraudRiskResult:
        return FraudRiskResult(
            invoice=invoice,
            shared_iban=self.accounts_repo.is_iban_shared_across_accounts(
                invoice.issuing_account_id, invoice.beneficiary_iban
            ),
            amount_inconsistent=self.activity_cost_ranges.get_amount_threshold_for_account(
                invoice.issuing_account_id
            )
            < invoice.amount,
        )

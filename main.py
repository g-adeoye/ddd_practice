from fastapi import FastAPI, HTTPException, Depends
from .domain.models import Transaction, RiskResult, Invoice
from .domain.use_cases import RiskScorer, InvoiceFraudDetector
from .adapters.in_memory import (
    InMemoryAdapter,
    CrossAccountIbanAdapter,
    ActivityAdapter,
)
from .domain.errors import UnknownAccount, InvalidAmount
from pydantic import BaseModel

app = FastAPI()


def get_risk_scorer() -> RiskScorer:

    adapter = InMemoryAdapter({1234: {"FRXXX", "FR345"}})
    risk_scorer = RiskScorer(2000, adapter)

    return risk_scorer


def get_fraud_detector() -> InvoiceFraudDetector:
    lookup_adapter = CrossAccountIbanAdapter({})
    activity_adapter = ActivityAdapter({})

    return InvoiceFraudDetector(lookup_adapter, activity_adapter)


class InvoiceCheckRequest(BaseModel):
    invoice_id: int
    issuing_account_id: str
    beneficiary_iban: str
    amount: int


class FraudRiskResponse(BaseModel):
    flagged: bool
    is_iban_shared_across_accounts: bool
    exceeds_amount_threshold: bool


@app.post("/risk-scorer", response_model=RiskResult)
def risk_scorer_endpoint(
    transaction: Transaction, risk_scorer: RiskScorer = Depends(get_risk_scorer)
) -> RiskResult:
    try:
        result = risk_scorer.evaluate(transaction)
    except UnknownAccount as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidAmount as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@app.post("/invoice-fraud-detector", response_model=FraudRiskResponse)
def fraud_risk_endpoint(
    req: InvoiceCheckRequest,
    fraud_detector: InvoiceFraudDetector = Depends(get_fraud_detector),
) -> FraudRiskResponse:
    invoice = Invoice(**req.model_dump())
    result = fraud_detector.evaluate(invoice)

    return FraudRiskResponse(
        flagged=result.flagged,
        is_iban_shared_across_accounts=result.shared_iban,
        exceeds_amount_threshold=result.amount_inconsistent,
    )

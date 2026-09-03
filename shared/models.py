from decimal import Decimal
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class RiskBand(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class QuoteRequest(BaseModel):
    loanAmount: Decimal = Field(..., gt=0, le=10_000_000, decimal_places=2)
    loanTermInMonths: int = Field(..., ge=1, le=360)
    riskBand: RiskBand


class QuoteResponse(BaseModel):
    quoteId: str
    commissionRate: Decimal
    totalCommission: Decimal


# Base commission rates by risk band (higher risk → higher commission).
BASE_RATES: dict[RiskBand, Decimal] = {
    RiskBand.A: Decimal("0.0150"),
    RiskBand.B: Decimal("0.0225"),
    RiskBand.C: Decimal("0.0350"),
    RiskBand.D: Decimal("0.0500"),
}

TERM_BONUS_PER_YEAR = Decimal("0.0010")
MAX_TERM_BONUS = Decimal("0.0100")


def calculate_quote(request: QuoteRequest) -> QuoteResponse:
    """Deterministic commission quote used by the mock vendor API."""
    base_rate = BASE_RATES[request.riskBand]
    years = request.loanTermInMonths // 12
    term_bonus = min(TERM_BONUS_PER_YEAR * years, MAX_TERM_BONUS)
    commission_rate = (base_rate + term_bonus).quantize(Decimal("0.0001"))
    total_commission = (request.loanAmount * commission_rate).quantize(Decimal("0.01"))
    return QuoteResponse(
        quoteId=str(uuid4()),
        commissionRate=commission_rate,
        totalCommission=total_commission,
    )

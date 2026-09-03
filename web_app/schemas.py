from decimal import Decimal

from pydantic import BaseModel, Field

from shared.models import RiskBand


class GenerateQuoteRequest(BaseModel):
    loanAmount: Decimal = Field(..., gt=0, le=10_000_000)
    loanTermInMonths: int = Field(..., ge=1, le=360)
    riskBand: RiskBand


class GenerateQuoteResponse(BaseModel):
    quoteId: str
    commissionRate: Decimal
    totalCommission: Decimal
    loanAmount: Decimal
    loanTermInMonths: int
    riskBand: RiskBand

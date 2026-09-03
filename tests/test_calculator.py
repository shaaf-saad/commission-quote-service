from decimal import Decimal

import pytest

from shared.models import QuoteRequest, RiskBand, calculate_quote


def test_band_a_short_term_uses_base_rate_only():
    quote = calculate_quote(
        QuoteRequest(loanAmount=Decimal("100000.00"), loanTermInMonths=11, riskBand=RiskBand.A)
    )
    assert quote.commissionRate == Decimal("0.0150")
    assert quote.totalCommission == Decimal("1500.00")
    assert quote.quoteId


def test_longer_term_adds_capped_bonus():
    quote = calculate_quote(
        QuoteRequest(loanAmount=Decimal("200000.00"), loanTermInMonths=360, riskBand=RiskBand.D)
    )
    # D base 0.0500 + min(30 years * 0.0010, 0.0100) = 0.0600
    assert quote.commissionRate == Decimal("0.0600")
    assert quote.totalCommission == Decimal("12000.00")


def test_rejects_invalid_loan_amount():
    with pytest.raises(Exception):
        QuoteRequest(loanAmount=Decimal("0"), loanTermInMonths=12, riskBand=RiskBand.A)

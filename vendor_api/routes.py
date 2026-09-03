import os
import random

from fastapi import APIRouter, Depends, HTTPException, status

from shared.models import QuoteRequest, QuoteResponse, calculate_quote
from vendor_api.auth import require_api_key

router = APIRouter()


def failure_rate() -> float:
    return float(os.getenv("VENDOR_FAILURE_RATE", "0.2"))


@router.post("/quotes", response_model=QuoteResponse)
def create_quote(
    payload: QuoteRequest,
    _: str = Depends(require_api_key),
) -> QuoteResponse:
    """Mock vendor endpoint. Requires api-key and randomly fails to simulate outages."""
    if random.random() < failure_rate():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Commission Quote vendor is temporarily unavailable. Please retry.",
        )
    return calculate_quote(payload)

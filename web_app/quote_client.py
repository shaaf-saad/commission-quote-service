from dataclasses import dataclass

import httpx

from shared.models import QuoteRequest, QuoteResponse
from web_app.config import settings


class QuoteClientError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class QuoteClient:
    base_url: str
    api_key: str
    timeout_seconds: float
    transport: httpx.BaseTransport | None = None

    def create_quote(self, request: QuoteRequest) -> QuoteResponse:
        try:
            with httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout_seconds,
                transport=self.transport,
            ) as client:
                response = client.post(
                    "/quotes",
                    json=request.model_dump(mode="json"),
                    headers={"api-key": self.api_key},
                )
        except httpx.TimeoutException as exc:
            raise QuoteClientError(
                "The Commission Quote API timed out. Please try again.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise QuoteClientError(
                "Unable to reach the Commission Quote API. Is the vendor service running?",
                status_code=503,
            ) from exc

        if response.status_code == 401:
            raise QuoteClientError("Vendor rejected the request: invalid API key.", status_code=502)
        if response.status_code == 422:
            raise QuoteClientError("Vendor rejected the loan details as invalid.", status_code=400)
        if response.status_code >= 500:
            detail = _extract_detail(response) or "The Commission Quote API failed. Please retry."
            raise QuoteClientError(detail, status_code=502)
        if response.status_code >= 400:
            detail = _extract_detail(response) or "Quote generation failed."
            raise QuoteClientError(detail, status_code=response.status_code)

        return QuoteResponse.model_validate(response.json())


def _extract_detail(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    return None


def default_client() -> QuoteClient:
    return QuoteClient(
        base_url=settings.vendor_api_url,
        api_key=settings.vendor_api_key,
        timeout_seconds=settings.vendor_timeout_seconds,
    )

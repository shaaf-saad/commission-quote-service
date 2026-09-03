from dataclasses import dataclass, field
from functools import lru_cache

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
    _client: httpx.Client = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            transport=self.transport,
        )

    def create_quote(self, request: QuoteRequest) -> QuoteResponse:
        try:
            response = self._client.post(
                "/quotes",
                json=request.model_dump(mode="json"),
                headers={"api-key": self.api_key},
            )
        except httpx.TimeoutException as exc:
            raise QuoteClientError(
                "The quote service took too long to respond. Please try again.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise QuoteClientError(
                "The quote service is temporarily unavailable. Please try again.",
                status_code=503,
            ) from exc

        if response.status_code == 401:
            raise QuoteClientError("The quote service could not authenticate the request.", status_code=502)
        if response.status_code == 422:
            raise QuoteClientError("The quote service could not process these loan details.", status_code=400)
        if response.status_code >= 500:
            raise QuoteClientError("The quote service is temporarily unavailable. Please try again.", status_code=502)
        if response.status_code >= 400:
            raise QuoteClientError("The quote could not be generated. Please check the details and try again.", status_code=response.status_code)

        return QuoteResponse.model_validate(response.json())


@lru_cache(maxsize=1)
def default_client() -> QuoteClient:
    return QuoteClient(
        base_url=settings.vendor_api_url,
        api_key=settings.vendor_api_key,
        timeout_seconds=settings.vendor_timeout_seconds,
    )

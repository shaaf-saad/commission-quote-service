import json

import httpx
from fastapi.testclient import TestClient

from web_app.main import app, get_quote_client
from web_app.quote_client import QuoteClient


def _client_with_handler(handler) -> TestClient:
    transport = httpx.MockTransport(handler)
    quote_client = QuoteClient(
        base_url="http://vendor.test",
        api_key="test-key",
        timeout_seconds=1.0,
        transport=transport,
    )
    app.dependency_overrides[get_quote_client] = lambda: quote_client
    return TestClient(app)


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_web_app_validation_rejects_bad_term():
    client = TestClient(app)
    response = client.post(
        "/api/quotes",
        json={"loanAmount": "1000.00", "loanTermInMonths": 0, "riskBand": "A"},
    )
    assert response.status_code == 422


def test_web_app_validation_rejects_amount_with_more_than_two_decimals():
    client = TestClient(app)
    response = client.post(
        "/api/quotes",
        json={"loanAmount": "1000.001", "loanTermInMonths": 12, "riskBand": "A"},
    )
    assert response.status_code == 422


def test_web_app_success_maps_vendor_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("api-key") == "test-key"
        body = json.loads(request.content)
        assert body["riskBand"] == "A"
        return httpx.Response(
            200,
            json={
                "quoteId": "q-123",
                "commissionRate": "0.0150",
                "totalCommission": "150.00",
            },
        )

    client = _client_with_handler(handler)
    response = client.post(
        "/api/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 24, "riskBand": "A"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quoteId"] == "q-123"
    assert body["loanAmount"] == "10000.00"
    assert body["riskBand"] == "A"


def test_web_app_surfaces_vendor_outage():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            json={"detail": "Commission Quote vendor is temporarily unavailable. Please retry."},
        )

    client = _client_with_handler(handler)
    response = client.post(
        "/api/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 24, "riskBand": "A"},
    )
    assert response.status_code == 502
    assert "unavailable" in response.json()["detail"].lower()


def test_web_app_handles_timeout():
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out")

    client = _client_with_handler(handler)
    response = client.post(
        "/api/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 24, "riskBand": "A"},
    )
    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()

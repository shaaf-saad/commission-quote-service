from decimal import Decimal

from fastapi.testclient import TestClient

from vendor_api.main import app


def test_health():
    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"


def test_rejects_missing_api_key(monkeypatch):
    monkeypatch.setenv("VENDOR_FAILURE_RATE", "0")
    client = TestClient(app)
    response = client.post(
        "/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 12, "riskBand": "A"},
    )
    assert response.status_code == 401
    assert "api-key" in response.json()["detail"]


def test_rejects_invalid_api_key(monkeypatch):
    monkeypatch.setenv("VENDOR_FAILURE_RATE", "0")
    monkeypatch.setenv("VENDOR_API_KEY", "expected-key")
    client = TestClient(app)
    response = client.post(
        "/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 12, "riskBand": "A"},
        headers={"api-key": "wrong"},
    )
    assert response.status_code == 401


def test_returns_quote_when_authenticated(monkeypatch):
    monkeypatch.setenv("VENDOR_FAILURE_RATE", "0")
    monkeypatch.setenv("VENDOR_API_KEY", "test-key")
    client = TestClient(app)
    response = client.post(
        "/quotes",
        json={"loanAmount": "100000.00", "loanTermInMonths": 12, "riskBand": "B"},
        headers={"api-key": "test-key"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quoteId"]
    assert Decimal(str(body["commissionRate"])) == Decimal("0.0235")
    assert Decimal(str(body["totalCommission"])) == Decimal("2350.00")


def test_randomly_simulates_vendor_outage(monkeypatch):
    monkeypatch.setenv("VENDOR_FAILURE_RATE", "1")
    monkeypatch.setenv("VENDOR_API_KEY", "test-key")
    client = TestClient(app)
    response = client.post(
        "/quotes",
        json={"loanAmount": "10000.00", "loanTermInMonths": 12, "riskBand": "A"},
        headers={"api-key": "test-key"},
    )
    assert response.status_code == 503

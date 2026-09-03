# Commission Quote App

Staff web app for generating commission quotes from loan details, plus a mock vendor **Commission Quote API**. The vendor is treated as an external system: it is a separate process, requires an `api-key` header, and randomly fails to simulate outages.

## Architecture

```
Browser  →  Web app (:8000)  →  Vendor API (:8001)
              │                      │
              │  /api/quotes         │  POST /quotes
              │  (validates input,   │  requires api-key
              │   holds API key)     │  ~20% random 503
```

The browser never sees the vendor API key. The web app is a small backend-for-frontend: it validates loan details, calls the vendor with `httpx`, and maps timeouts / 401 / 5xx into user-facing errors.

Commission is calculated deterministically in `shared/models.py` so the mock is testable:

| Risk band | Base rate |
|-----------|-----------|
| A | 1.50% |
| B | 2.25% |
| C | 3.50% |
| D | 5.00% |

A term bonus of 0.10% is added per full year of term, capped at 1.00%.  
`totalCommission = loanAmount × commissionRate`.

## Prerequisites

- Python 3.11+ recommended (3.10+ should work)
- Two terminal windows (vendor API + web app)

## Setup

From this directory (`commission-quote-app`):

```bash
python -m venv .venv
```

Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` defaults:

- `VENDOR_API_KEY` — shared secret the web app sends as the `api-key` header
- `VENDOR_API_URL` — vendor base URL (`http://127.0.0.1:8001`)
- `VENDOR_FAILURE_RATE` — probability of a simulated vendor 503 (`0.2` = 20%)
- `VENDOR_TIMEOUT_SECONDS` — web app HTTP timeout when calling the vendor

## Run

Start the mock vendor first.

```bash
python -m uvicorn vendor_api.main:app --host 127.0.0.1 --port 8001
```

In a second terminal (same venv, same directory):

```bash
python -m uvicorn web_app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Submit `loanAmount`, `loanTermInMonths`, and `riskBand`, then use **Generate Quote**.

If quotes fail with “Unable to reach the Commission Quote API”, the vendor process is not running. If they fail with a 503-style retry message, that is the intentional random outage — submit again.

To disable random vendor failures while demoing:

```powershell
$env:VENDOR_FAILURE_RATE="0"
python -m uvicorn vendor_api.main:app --host 127.0.0.1 --port 8001
```

## Tests

```bash
python -m pytest -q
```

Coverage is focused on:

- Commission formula and invalid loan amounts
- Vendor API key enforcement and simulated outages
- Web app validation, successful mapping of a vendor quote, vendor outage, and timeout

## Edge cases handled

- Non-positive / oversized loan amounts and terms (client + Pydantic on both services)
- Missing or invalid vendor `api-key` → 401 from vendor; web app does not expose the key
- Random vendor 503
- Vendor timeout and connection errors
- Frontend loading state, disabled submit, and `aria-live` result region

## AI usage

I used Cursor (Grok) as a pairing assistant for this take-home:

- Scaffolded the FastAPI vendor + web app layout, pytest cases, and the HTML/CSS/JS UI
- I chose the split (separate vendor process, API key only on the server, deterministic calculator in `shared/`) so the next live-coding round can add auth, persistence, or a real vendor client without rewriting the UI
- I reviewed and adjusted validation, error mapping, and tests rather than pasting an unexamined generated app

## Trade-offs

- Two processes instead of one in-process fake: closer to the real vendor boundary, slightly more setup
- Vanilla frontend instead of React: less ceremony for a 4-hour exercise; easy to replace later
- Random failures are not retried automatically: staff see the error and can resubmit (retry policy would be a natural follow-up)

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

The browser never sees the vendor API key. The web app is a small backend-for-frontend: it validates loan details, calls the vendor with `httpx`, and maps timeouts / 401 / 5xx into user-facing errors. The UI is a React application styled with Tailwind CSS; TanStack Query manages the quote mutation state.

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
- Bun 1.0+ for the React frontend
- Two terminal windows for the backend services (plus an optional third for frontend development)

## Setup

From this directory (`commission-quote-service`):

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

Install frontend dependencies:

```bash
cd frontend
bun install
cd ..
```

`.env` defaults:

- `VENDOR_API_KEY` — shared secret the web app sends as the `api-key` header
- `VENDOR_API_URL` — vendor base URL (`http://127.0.0.1:8001`)
- `VENDOR_FAILURE_RATE` — probability of a simulated vendor 503 (`0.2` = 20%)
- `VENDOR_TIMEOUT_SECONDS` — web app HTTP timeout when calling the vendor
- `ALLOWED_ORIGINS` — comma-separated browser origins allowed to call the BFF

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

The production frontend is served by FastAPI from `web_app/static`. After changing React code, rebuild it with:

```bash
cd frontend
bun run build
```

For frontend development with hot reload, keep the web app running on port 8000 and use a third terminal:

```bash
cd frontend
bun run dev
```

Open the Vite URL shown in the terminal. Its `/api` requests are proxied to the FastAPI BFF.

## GitHub Pages

The React UI can also be deployed to GitHub Pages using `.github/workflows/deploy-pages.yml`. Enable **GitHub Pages > Source: GitHub Actions** in the repository settings. The workflow builds the frontend with Bun on pushes to `main`.

GitHub Pages only hosts static files, so the FastAPI BFF and vendor API must be deployed separately. Set the repository variable `VITE_API_BASE_URL` to the public BFF URL, for example `https://api.example.com`, and add the Pages origin to the BFF's `ALLOWED_ORIGINS`, for example `https://your-user.github.io` or `https://your-user.github.io/commission-quote-service`.

If `VITE_API_BASE_URL` is not configured, the Pages workflow enables a clearly labeled interactive demo mode. It uses the same rate formula in the browser for presentation purposes, but does not call the vendor API. Configure the variable when a public BFF is available to switch the page to live mode.

The vendor API key remains private because it is held by the BFF and is never included in the React build.

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

Frontend checks:

```bash
cd frontend
bun run lint
bun run build
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

## Technology choices

- **React** provides a small component model for keeping the form and result states readable as the UI grows. Plain JavaScript would have less setup, but would make state transitions and future screens harder to organize.
- **Tailwind CSS** gives the UI consistent responsive styling without introducing a larger component framework. A component library would add more dependencies than this focused workflow needs.
- **TanStack Query** handles the quote mutation lifecycle and keeps loading, success, and error behavior explicit. Native `fetch` is sufficient for one request, but TanStack Query gives the frontend a clear path to retries, caching, and additional server state.
- **Bun** is used as the frontend package manager and runtime because it provides fast installs and scripts. Node.js would work equally well, but Bun keeps the frontend toolchain lightweight for this project.
- **FastAPI** was retained for the BFF and mock vendor because it already provides typed request validation, dependency injection, and straightforward HTTP endpoints in the existing Python codebase. Django would be better suited to a larger database-backed product, while Flask would require more validation and API structure to be added manually.
- **HTTPX** handles BFF-to-vendor calls with timeouts and injectable transports for tests. It fits the Python service and makes vendor failure scenarios easy to exercise.

## AI usage

I used Cursor (Grok) as a pairing assistant for this take-home:

- Scaffolded the React frontend, Tailwind styling, TanStack Query wiring, pytest cases, and supporting API structure
- I chose the split (separate vendor process, API key only on the server, deterministic calculator in `shared/`) so the next live-coding round can add auth, persistence, or a real vendor client without rewriting the UI
- I reviewed and adjusted validation, error mapping, and tests rather than pasting an unexamined generated app

## Trade-offs

- Two processes instead of one in-process fake: closer to the real vendor boundary, slightly more setup
- React frontend with Bun adds a build step, but provides clearer component boundaries and a scalable UI foundation
- Random failures are not retried automatically: staff see the error and can resubmit (retry policy would be a natural follow-up)

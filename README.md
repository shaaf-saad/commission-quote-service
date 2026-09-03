# Commission Quote App

Staff web app for generating commission quotes from loan details, plus a mock vendor **Commission Quote API**. The project demonstrates a UI plus backend-for-frontend (BFF) design while the real vendor service is still under construction.

## What this service does

Users enter a loan amount, term, and risk band. The application validates the details, sends them through the BFF to the authenticated mock vendor, and displays the returned quote. The vendor is intentionally a separate process, requires an `api-key` header, and randomly fails to simulate real network conditions.

The project has two backend services and one frontend:

- **Web app / BFF** (`web_app`) is the browser-facing service on port `8000`. It owns the vendor credential, validates requests, calls the vendor, and translates upstream failures into stable responses.
- **Mock vendor API** (`vendor_api`) runs on port `8001`. It enforces the API key, calculates commission, and returns an occasional `503` to model vendor downtime.
- **React frontend** (`frontend`) provides the form and result experience. In local development it uses Vite; the production build is served from `web_app/static`.

The BFF is deliberately the only service the browser needs to trust. This prevents a vendor secret from being bundled into JavaScript and gives the application one place to enforce its public contract.

## API contracts

### `POST /api/quotes` - BFF

Request:

```json
{
    "loanAmount": "100000.00",
    "loanTermInMonths": 12,
    "riskBand": "B"
}
```

Successful response:

```json
{
    "quoteId": "generated-uuid",
    "commissionRate": "0.0235",
    "totalCommission": "2350.00",
    "loanAmount": "100000.00",
    "loanTermInMonths": 12,
    "riskBand": "B"
}
```

Invalid input returns `422`. Vendor timeouts return `504`, connection failures return `503`, and vendor `5xx` responses are mapped to `502` so callers are not coupled to the vendor's error format.

### `POST /quotes` - mock vendor

The vendor accepts the same loan fields and requires:

```text
api-key: <server-side configured key>
```

Missing or invalid credentials return `401`. Valid requests return `quoteId`, `commissionRate`, and `totalCommission`. Amounts use `Decimal` rather than binary floating point to avoid currency rounding errors.

## Project structure

```text
frontend/             React, Vite, Tailwind, and TanStack Query
shared/models.py      Shared Pydantic contracts and commission calculation
web_app/main.py       Browser-facing BFF routes and static file serving
web_app/quote_client.py  HTTPX client for the vendor boundary
vendor_api/routes.py  Authenticated mock vendor endpoint
tests/                Calculator, vendor API, and BFF integration tests
.github/workflows/    GitHub Pages deployment workflow
```

## Architecture

```
Browser  →  Web app (:8000)  →  Vendor API (:8001)
              │                      │
              │  /api/quotes         │  POST /quotes
              │  (validates input,   │  requires api-key
              │   holds API key)     │  ~20% random 503
```

The browser never sees the vendor API key. The web app is a small backend-for-frontend: it validates loan details, calls the vendor with `httpx`, and maps timeouts / 401 / 5xx into user-facing errors. The UI is a React application styled with Tailwind CSS; TanStack Query manages the quote mutation state.

### Request flow

1. The React form validates the amount, term, and risk band before submitting.
2. React sends `POST /api/quotes` to the FastAPI BFF. TanStack Query exposes pending, success, and error states to the UI.
3. The BFF validates the payload again with Pydantic. The browser never receives the vendor credential.
4. The BFF calls `POST /quotes` on the vendor with the server-side `api-key` header.
5. The vendor validates authentication, calculates the quote, and may return a simulated `503` outage.
6. The BFF maps vendor responses into a stable browser response and user-friendly error status.

### Layer responsibilities

| Layer | Responsibility |
|-------|----------------|
| React + Tailwind | Form, responsive UI, accessibility, and quote states |
| TanStack Query | Quote mutation lifecycle and server-state handling |
| FastAPI BFF | Public API, validation, secret handling, timeout/error mapping |
| HTTPX client | Outbound vendor request with connection reuse and timeout support |
| Mock vendor API | API-key enforcement, deterministic commission calculation, random outages |
| Shared models | Pydantic contracts, Decimal calculations, and risk-band rules |

For local development, Vite proxies `/api` to the BFF. For GitHub Pages, the static React build uses `VITE_API_BASE_URL` for a separately hosted BFF, or uses the labeled client-side demo mode when that variable is not configured.

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

If `VITE_API_BASE_URL` is not configured, the Pages workflow enables a clearly labeled interactive demo mode with the same `0.5` (50%) simulated failure rate used for local demonstrations. It uses the same rate formula in the browser for presentation purposes, but does not call the vendor API. Configure the variable when a public BFF is available to switch the page to live mode.

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

| Technology | Why it was chosen | Why not the main alternatives |
|------------|-------------------|-------------------------------|
| React | Component boundaries keep form and result states easy to extend. | Plain JavaScript has less setup, but becomes harder to organize as screens grow. |
| Tailwind CSS | Fast, consistent responsive styling without a large component framework. | A UI library would add more dependencies than this focused workflow needs. |
| TanStack Query | Makes mutation pending, success, and error states explicit, with a path to retries and caching. | Native `fetch` would work for one request but provides less structure for future server state. |
| Bun | Fast frontend installs and scripts with a compact toolchain. | Node.js would work equally well; Bun was selected for the requested alternative runtime. |
| FastAPI | Already fits the Python codebase and provides validation, dependency injection, and clear HTTP endpoints. | Django is better for a larger database-backed product; Flask would need more API structure added manually. |
| HTTPX | Supports timeouts, connection reuse, and injectable transports for tests. | A lower-level HTTP client would add implementation detail without helping this service. |

## Architecture Decision Records (ADRs)

ADRs capture important technical decisions in a lightweight, reviewable format. A typical ADR records:

1. **Title and status** - what decision is being recorded and whether it is proposed, accepted, superseded, or deprecated.
2. **Context** - the problem, constraints, and forces that shaped the decision.
3. **Decision** - the option selected and how it will work.
4. **Alternatives considered** - credible options that were rejected and why.
5. **Consequences** - the benefits, trade-offs, and follow-up risks created by the decision.

The records below document the decisions made for this take-home service.

### ADR-001: Use a FastAPI backend-for-frontend

**Status:** Accepted

**Context:** The browser needs a stable API, while the vendor API is external, authenticated, and expected to fail occasionally. The vendor API key must not be exposed to browser code.

**Decision:** Use the FastAPI web app as a backend-for-frontend. It validates browser requests, stores the vendor configuration on the server, calls the vendor through HTTPX, and maps upstream errors into a stable public response.

**Alternatives considered:**

- Direct browser-to-vendor calls were rejected because they would expose the API key and couple the UI to vendor behavior.
- A single in-process mock was rejected because a separate vendor process better represents the real integration boundary.
- A Node.js BFF was not chosen because the existing service and tests are Python-based and FastAPI already provides the needed API features.

**Benefits:** Secret isolation, a single public contract, centralized validation and error mapping, and an easy path to replace the mock vendor with a real integration.

**Consequences:** There are two backend processes to run and one additional network hop. The BFF must be monitored and tested as an integration boundary.

### ADR-002: Use React, Tailwind CSS, and TanStack Query for the UI

**Status:** Accepted

**Context:** The UI needs a form, accessible loading and error states, responsive presentation, and a foundation that can grow beyond one screen without becoming difficult to maintain.

**Decision:** Use React for component boundaries, Tailwind CSS for responsive styling, and TanStack Query for the quote mutation lifecycle. Keep the API call in a small dedicated module and keep the vendor key out of the frontend build.

**Alternatives considered:**

- Vanilla JavaScript and CSS were rejected for the final UI because state transitions and future screens would become more tightly coupled to DOM manipulation.
- Vue was not chosen because React was the requested direction and the existing UI could be migrated directly to it with minimal backend change.
- A component library was not chosen because this focused workflow does not need its larger dependency and styling surface.
- Plain `fetch` was sufficient technically, but TanStack Query was chosen to make server-state behavior explicit and leave room for retries, caching, and additional requests.

**Benefits:** Clear component ownership, consistent styling, explicit request states, responsive design, and a scalable frontend foundation.

**Consequences:** The frontend now has a JavaScript build step and dependency management. TanStack Query is more capability than the single mutation strictly requires, but it avoids inventing request-state conventions as the UI expands.

### ADR-003: Use Bun with Vite for frontend tooling

**Status:** Accepted

**Context:** The React frontend needs dependency installation, a development server, a production build, and a repeatable GitHub Pages workflow. The backend remains Python-based.

**Decision:** Use Bun as the frontend package manager and script runtime, with Vite for development and production builds.

**Alternatives considered:**

- Node.js with npm would be a conventional and valid choice, but Bun provides a fast, compact workflow and meets the project requirement to use an alternative to Node.js.
- A framework such as Next.js was not chosen because server rendering and framework routing are unnecessary for this small static UI hosted behind a separate BFF.

**Benefits:** Fast installs, simple scripts, Vite's quick feedback loop, and a small static deployment artifact for GitHub Pages.

**Consequences:** Contributors need Bun for frontend development, while Python is still required for the backend. The project documents both toolchains explicitly.

### ADR-004: Keep the mock vendor as a separate service

**Status:** Accepted

**Context:** The real Commission Quote API is unavailable, but its authentication and payload contract are finalized. Development should exercise the same boundary the production service will use.

**Decision:** Run a separate FastAPI vendor process with API-key enforcement, deterministic Decimal-based calculations, and configurable random `503` failures.

**Alternatives considered:**

- A function call inside the BFF would be simpler, but would not test HTTP transport, authentication headers, timeouts, or upstream status handling.
- A third-party mock server would add another dependency and make the business calculation less visible for reviewers.

**Benefits:** Realistic integration behavior, deterministic tests when failures are disabled, explicit security testing, and easy replacement with the future vendor endpoint.

**Consequences:** Local setup requires another process and the intentional random failure can make demos appear unreliable unless `VENDOR_FAILURE_RATE=0` is used.

### ADR-005: Deploy the UI to GitHub Pages with an optional demo mode

**Status:** Accepted

**Context:** GitHub Pages is useful for sharing the UI, but it cannot run Python services. A public BFF may not be available when the static site is reviewed.

**Decision:** Build the React UI as a GitHub Pages artifact. When `VITE_API_BASE_URL` is configured, it calls the live BFF. Otherwise, the page uses a clearly labeled client-side demo calculation for presentation only.

**Alternatives considered:**

- Hosting the full stack on GitHub Pages was rejected because Pages only serves static files.
- Showing a static screenshot was rejected because reviewers should be able to interact with the form.
- Calling the vendor directly from Pages was rejected because it would expose the vendor key.

**Benefits:** A shareable interactive demonstration without requiring backend hosting, while preserving a straightforward path to live BFF integration.

**Consequences:** Demo mode is not a substitute for the authenticated vendor flow. A live deployment requires a separately hosted BFF, configured CORS, and a public `VITE_API_BASE_URL`.

## AI usage

I used Cursor (Grok) as a pairing assistant for this take-home:

- Scaffolded the React frontend, Tailwind styling, TanStack Query wiring, pytest cases, and supporting API structure
- I chose the split (separate vendor process, API key only on the server, deterministic calculator in `shared/`) so the next live-coding round can add auth, persistence, or a real vendor client without rewriting the UI
- I reviewed and adjusted validation, error mapping, and tests rather than pasting an unexamined generated app

## Trade-offs

- Two processes instead of one in-process fake: closer to the real vendor boundary, slightly more setup
- React frontend with Bun adds a build step, but provides clearer component boundaries and a scalable UI foundation
- Random failures are not retried automatically: staff see the error and can resubmit (retry policy would be a natural follow-up)

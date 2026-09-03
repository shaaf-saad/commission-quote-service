from pathlib import Path
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from shared.models import QuoteRequest
from web_app.quote_client import QuoteClient, QuoteClientError, default_client
from web_app.schemas import GenerateQuoteRequest, GenerateQuoteResponse
from web_app.config import settings

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Commission Quote App",
    description="Staff app for generating commission quotes via the vendor API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
    expose_headers=["X-Correlation-ID"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def add_correlation_id(request: Request, call_next) -> Response:
    correlation_id = str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


def get_quote_client() -> QuoteClient:
    return default_client()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "web-app"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/quotes", response_model=GenerateQuoteResponse)
def generate_quote(
    payload: GenerateQuoteRequest,
    client: QuoteClient = Depends(get_quote_client),
) -> GenerateQuoteResponse:
    try:
        quote = client.create_quote(QuoteRequest.model_validate(payload.model_dump()))
    except QuoteClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    return GenerateQuoteResponse(
        quoteId=quote.quoteId,
        commissionRate=quote.commissionRate,
        totalCommission=quote.totalCommission,
        loanAmount=payload.loanAmount,
        loanTermInMonths=payload.loanTermInMonths,
        riskBand=payload.riskBand,
    )

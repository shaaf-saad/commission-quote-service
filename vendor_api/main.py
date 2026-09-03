from fastapi import FastAPI

from vendor_api.routes import router

app = FastAPI(
    title="Commission Quote Vendor API (Mock)",
    description="Simulated external vendor used by the lending platform.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "vendor-api"}

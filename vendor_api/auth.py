import os
from typing import Annotated

from fastapi import Header, HTTPException, status

API_KEY_HEADER = "api-key"


def expected_api_key() -> str:
    return os.getenv("VENDOR_API_KEY", "dev-vendor-api-key")


def require_api_key(api_key: Annotated[str | None, Header(alias=API_KEY_HEADER)] = None) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing api-key header",
        )
    if api_key != expected_api_key():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid api-key",
        )
    return api_key

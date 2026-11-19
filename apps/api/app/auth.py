import time
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import Settings

JWKS_TTL_SECONDS = 600
_jwks_cache: dict = {"fetched_at": 0.0, "keys": []}


@dataclass(frozen=True)
class SupabaseClaims:
    sub: str
    email: str | None
    role: str | None


def unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def _fetch_jwks(settings: Settings) -> list[dict]:
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json().get("keys", [])


async def _jwks(settings: Settings, *, force_refresh: bool = False) -> list[dict]:
    age = time.monotonic() - _jwks_cache["fetched_at"]
    if not force_refresh and _jwks_cache["keys"] and age < JWKS_TTL_SECONDS:
        return _jwks_cache["keys"]
    keys = await _fetch_jwks(settings)
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = time.monotonic()
    return keys


def _key_for(kid: str | None, keys: list[dict]) -> dict | None:
    for key in keys:
        if key.get("kid") == kid:
            return key
    return None


def reset_jwks_cache() -> None:
    _jwks_cache["keys"] = []
    _jwks_cache["fetched_at"] = 0.0


async def verify_supabase_jwt(token: str, settings: Settings) -> SupabaseClaims:
    """Verify signature, audience and expiry; the caller reads the role from Postgres."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise unauthorized("Malformed token") from exc

    algorithm = header.get("alg")
    if algorithm == "HS256":
        if not settings.supabase_jwt_secret:
            raise unauthorized("Token signing is not configured")
        key: object = settings.supabase_jwt_secret
    else:
        key = _key_for(header.get("kid"), await _jwks(settings))
        if key is None:
            key = _key_for(header.get("kid"), await _jwks(settings, force_refresh=True))
        if key is None:
            raise unauthorized("Unknown signing key")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=settings.supabase_jwt_aud,
        )
    except JWTError as exc:
        raise unauthorized("Invalid or expired token") from exc

    subject = payload.get("sub")
    if not subject:
        raise unauthorized("Token has no subject")
    return SupabaseClaims(
        sub=str(subject),
        email=payload.get("email"),
        role=payload.get("role"),
    )

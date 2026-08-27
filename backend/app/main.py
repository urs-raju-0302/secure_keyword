from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes import auth, documents, keys, search
from app.config import get_settings

logger = logging.getLogger("secure_keyword")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Permissions-Policy"] = "geolocation=()"
        return response


# Simple in-memory rate limiter (educational; use Redis/WAF in production)
_rate_buckets: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.environment == "test":
            return await call_next(request)
        path = request.url.path
        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/search"):
            client = request.client.host if request.client else "unknown"
            key = f"{client}:{path}"
            now = time.time()
            window = 60.0
            limit = 30 if "search" in path else 10
            bucket = [t for t in _rate_buckets[key] if now - t < window]
            if len(bucket) >= limit:
                return Response(content='{"detail":"Too many requests"}', status_code=429, media_type="application/json")
            bucket.append(now)
            _rate_buckets[key] = bucket
        return await call_next(request)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Secure Keyword Search API",
        description=(
            "Educational searchable-encryption and key-management demonstration. "
            "HMAC-SHA-256 search tokens protect plaintext keywords from the index, "
            "but deterministic tokens leak equality of repeated queries."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(search.router, prefix="/api/v1")
    app.include_router(keys.router, prefix="/api/v1")
    app.include_router(keys.audit_router, prefix="/api/v1")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.on_event("startup")
    def on_startup():
        if settings.environment == "test":
            return
        from app.db import SessionLocal
        from app.services.key_management_service import KeyManagementService

        db = SessionLocal()
        try:
            kms = KeyManagementService(db, settings)
            kms.ensure_bootstrap_keys()
            db.commit()
        except Exception as exc:
            logger.warning("Key bootstrap deferred: %s", type(exc).__name__)
            db.rollback()
        finally:
            db.close()

    return app


app = create_app()

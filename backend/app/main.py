"""
The Lenny Growth Assistant — FastAPI Application
Main entry point with middleware, startup/shutdown, and route registration.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import logging
import time

from app.config import settings
from app.db.database import init_db, close_db
from app.api import health, sessions, messages, config_routes


# ─── Structured Logging Setup ──────────────────────────

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.APP_ENV == "development"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(
        logging.getLevelName(settings.LOG_LEVEL.upper())
    ),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ─── Lifespan (startup/shutdown) ────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — handles startup and shutdown."""
    logger.info(
        "application_starting",
        env=settings.APP_ENV,
        llm_provider=settings.LLM_PROVIDER,
    )

    # Startup: initialize database
    try:
        await init_db()
        logger.info("database_ready")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        # Don't crash — allow the app to start in degraded mode
        # Health endpoint will report the issue

    yield

    # Shutdown: close connections
    await close_db()
    logger.info("application_shutdown")


# ─── FastAPI App ────────────────────────────────────────

app = FastAPI(
    title="The Lenny Growth Assistant",
    description="AI-powered conversational assistant grounded in Lenny's Podcast transcripts.",
    version="0.1.0",
    lifespan=lifespan,
)


# ─── CORS Middleware ────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request Logging Middleware ─────────────────────────

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)

    if request.url.path != "/health":  # Don't log health checks
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )

    return response


# ─── Global Exception Handler ──────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again.",
                "details": {"type": type(exc).__name__} if settings.APP_ENV == "development" else {},
            }
        },
    )


# ─── Register Routes ───────────────────────────────────

app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(config_routes.router)


# ─── Root Redirect ──────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "The Lenny Growth Assistant API", "docs": "/docs"}

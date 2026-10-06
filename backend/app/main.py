from contextlib import asynccontextmanager
from time import monotonic
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.api.system import router as system_router
from app.core.config import (
    APP_VERSION,
    ASSISTANT_NAME,
    BUILD_STAGE,
    WAKE_PHRASE,
)
from app.core.logging_config import configure_logging, log_event
from app.runtime.assistant_runtime import assistant_runtime
from app.api.platform import router as platform_router
from app.api.account import router as account_router
from app.api.research import router as research_router
from app.core.config import BACKEND_DIR
from app.core.config import MOBILE_ACCESS_ENABLED, NAYA_DEVICE_TOKEN
from secrets import compare_digest


@asynccontextmanager
async def lifespan(application: FastAPI):

    del application

    configure_logging()
    log_event("application_starting", component="api")
    assistant_runtime.start()

    try:
        yield

    finally:
        assistant_runtime.stop()
        log_event("application_stopped", component="api")


app = FastAPI(
    title="MoneroAI API",
    description="Personal AI Assistant Backend",
    version=APP_VERSION,
    lifespan=lifespan,
)


app.include_router(
    chat_router,
    prefix="/api"
)

app.include_router(
    system_router,
    prefix="/api",
)

app.include_router(
    health_router,
    prefix="/api",
)
app.include_router(platform_router, prefix="/api")
app.include_router(account_router, prefix="/api")
app.include_router(research_router, prefix="/api")


@app.middleware("http")
async def request_diagnostics(request: Request, call_next):

    request_id = uuid4().hex
    request.state.request_id = request_id

    started_at = monotonic()

    try:
        response = await call_next(request)

    except Exception as error:
        duration_ms = round((monotonic() - started_at) * 1000, 1)
        log_event(
            "http_request_failed",
            level=40,
            component="api",
            duration_ms=duration_ms,
            error_type=type(error).__name__,
            method=request.method,
            path="<unhandled>",
            request_id=request_id,
            status_code=500,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error.",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    route = request.scope.get("route")
    route_path = getattr(route, "path", "<unmatched>")
    duration_ms = round((monotonic() - started_at) * 1000, 1)
    log_event(
        "http_request_completed",
        component="api",
        duration_ms=duration_ms,
        method=request.method,
        path=route_path,
        request_id=request_id,
        status_code=response.status_code,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def sanitized_validation_error(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:

    del error

    return JSONResponse(
        status_code=422,
        content={
            "detail": "The request body is invalid.",
            "request_id": getattr(
                request.state,
                "request_id",
                uuid4().hex,
            ),
        },
    )


@app.get("/")
def root():
    return {
        "message": f"MoneroAI is running with {ASSISTANT_NAME}.",
        "version": APP_VERSION,
        "build_stage": BUILD_STAGE,
        "assistant": ASSISTANT_NAME,
        "wake_phrase": WAKE_PHRASE,
        "google_access": "read_only",
        "client": "/app/",
    }


app.mount(
    "/app",
    StaticFiles(directory=BACKEND_DIR / "web", html=True),
    name="naya-client",
)


@app.middleware("http")
async def mobile_device_authentication(request: Request, call_next):
    if MOBILE_ACCESS_ENABLED and request.url.path.startswith("/api/"):
        public_paths = {"/api/health/live", "/api/auth/login", "/api/auth/register", "/api/plans"}
        if request.url.path not in public_paths:
            supplied = request.headers.get("X-Naya-Device-Token", "")
            if not NAYA_DEVICE_TOKEN or not compare_digest(supplied, NAYA_DEVICE_TOKEN):
                return JSONResponse(status_code=401, content={"detail": "Device pairing required."})
    return await call_next(request)

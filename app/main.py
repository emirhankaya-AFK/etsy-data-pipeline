import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.database import close_database, initialize_database
from app.services.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


def create_app(*, enable_runtime: bool = True) -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if enable_runtime:
            await initialize_database()
            start_scheduler(settings)
        yield
        if enable_runtime:
            stop_scheduler()
            await close_database()

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Scheduled Playwright collection with PostgreSQL history and analytics.",
        lifespan=lifespan,
    )
    application.add_middleware(GZipMiddleware, minimum_size=1_000)
    application.include_router(router)
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled application error", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    return application


app = create_app()

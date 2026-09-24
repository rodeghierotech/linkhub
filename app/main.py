"""Ponto de entrada da aplicação FastAPI."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth.dependencies import get_optional_user
from app.auth.router import router as auth_router
from app.database.database import run_migrations
from app.database.models import User
from app.links.router import router as links_router

APP_DIR = Path(__file__).resolve().parent


def create_app(*, migrate_on_start: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if migrate_on_start:
            run_migrations()
        yield

    application = FastAPI(title="LinkShort", lifespan=lifespan)
    application.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET", "local-development-change-me"),
        session_cookie="linkshort_session",
        max_age=60 * 60 * 24 * 14,
        same_site="lax",
        https_only=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    )
    application.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
    application.include_router(auth_router)
    application.include_router(links_router)

    @application.get("/")
    def home(current_user: User | None = Depends(get_optional_user)):
        destination = "/dashboard" if current_user else "/login"
        return RedirectResponse(destination, status_code=status.HTTP_303_SEE_OTHER)

    return application


app = create_app()

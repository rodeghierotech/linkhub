"""Páginas de cadastro, login e logout."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.dependencies import get_optional_user
from app.auth.schemas import RegistrationData
from app.auth.service import AuthError, AuthService
from app.database.database import get_db
from app.database.models import User
from app.utils.csrf import get_csrf_token, validate_csrf

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _auth_context(request: Request, *, error: str | None = None, email: str = "") -> dict:
    return {
        "error": error,
        "email": email,
        "csrf_token": get_csrf_token(request),
        "current_user": None,
    }


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    if current_user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "register.html", _auth_context(request))


@router.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirmation: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    try:
        user = AuthService(db).register(
            RegistrationData(name, email, password, password_confirmation)
        )
    except AuthError as exc:
        return templates.TemplateResponse(
            request,
            "register.html",
            _auth_context(request, error=str(exc), email=email),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    get_csrf_token(request)
    return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    if current_user:
        return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html", _auth_context(request))


@router.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    user = AuthService(db).authenticate(email, password)
    if user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            _auth_context(request, error="E-mail ou senha inválidos.", email=email),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    get_csrf_token(request)
    return RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    validate_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

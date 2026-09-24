"""Rotas privadas de links e redirecionamento público."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.analytics.service import AnalyticsService
from app.auth.dependencies import require_user
from app.database.database import get_db
from app.database.models import User
from app.links.service import InactiveLinkError, LinkInputError, LinkService
from app.utils.csrf import get_csrf_token, validate_csrf

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _base_context(request: Request, current_user: User) -> dict:
    return {
        "current_user": current_user,
        "csrf_token": get_csrf_token(request),
        "base_url": str(request.base_url).rstrip("/"),
    }


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    service = LinkService(db)
    analytics = AnalyticsService(db).dashboard(current_user.id)
    context = _base_context(request, current_user)
    context.update(
        links=service.list_links(current_user.id, limit=5),
        analytics=analytics,
        stats=analytics.stats,
        error=None,
    )
    return templates.TemplateResponse(request, "dashboard.html", context)


@router.get("/links", response_class=HTMLResponse)
def links_page(
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    context = _base_context(request, current_user)
    context.update(links=LinkService(db).list_links(current_user.id), error=None)
    return templates.TemplateResponse(request, "links.html", context)


@router.post("/links", response_class=HTMLResponse)
def create_link(
    request: Request,
    original_url: str = Form(...),
    custom_alias: str = Form(""),
    csrf_token: str = Form(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    service = LinkService(db)
    try:
        service.create_link(
            user_id=current_user.id,
            original_url=original_url,
            custom_alias=custom_alias,
        )
    except LinkInputError as exc:
        context = _base_context(request, current_user)
        context.update(links=service.list_links(current_user.id), error=str(exc))
        return templates.TemplateResponse(
            request, "links.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )
    return RedirectResponse("/links", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/links/{link_id}", response_class=HTMLResponse)
def link_detail(
    link_id: int,
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    analytics = AnalyticsService(db).link_detail(current_user.id, link_id)
    context = _base_context(request, current_user)
    context.update(link=analytics.link, analytics=analytics)
    return templates.TemplateResponse(request, "link_detail.html", context)


@router.post("/links/{link_id}/toggle")
def toggle_link(
    link_id: int,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    LinkService(db).toggle(link_id, current_user.id)
    return RedirectResponse("/links", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/links/{link_id}/delete")
def delete_link(
    link_id: int,
    request: Request,
    csrf_token: str = Form(...),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    validate_csrf(request, csrf_token)
    LinkService(db).delete(link_id, current_user.id)
    return RedirectResponse("/links", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/r/{short_code}")
def redirect_to_original(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        link = LinkService(db).register_click(
            short_code,
            user_agent=request.headers.get("user-agent"),
            referrer=request.headers.get("referer"),
        )
    except InactiveLinkError:
        return templates.TemplateResponse(
            request,
            "link_unavailable.html",
            {"current_user": None},
            status_code=status.HTTP_410_GONE,
        )
    return RedirectResponse(link.original_url, status_code=status.HTTP_302_FOUND)

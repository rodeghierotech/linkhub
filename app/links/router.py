"""Rotas HTTP: dashboard, criação, redirecionamento e exclusão."""

from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import HttpUrl, TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.links.service import LinkService

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

_url_adapter: TypeAdapter[HttpUrl] = TypeAdapter(HttpUrl)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, error: str | None = None, db: Session = Depends(get_db)):
    service = LinkService(db)
    links = service.list_links()
    stats = service.get_dashboard_stats()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "links": links,
            "stats": stats,
            "base_url": str(request.base_url).rstrip("/"),
            "error": error,
        },
    )


@router.post("/links")
def create_link(
    request: Request,
    original_url: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        validated = _url_adapter.validate_python(original_url)
    except ValidationError:
        return RedirectResponse(
            url="/?error=URL+inválida.+Informe+uma+URL+completa+(ex:+https://exemplo.com)",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    service = LinkService(db)
    service.create_link(str(validated))
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/r/{short_code}")
def redirect_to_original(short_code: str, db: Session = Depends(get_db)):
    service = LinkService(db)
    link = service.register_click(short_code)
    return RedirectResponse(url=link.original_url, status_code=status.HTTP_302_FOUND)


@router.post("/links/{link_id}/delete")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    service = LinkService(db)
    service.delete_link(link_id)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

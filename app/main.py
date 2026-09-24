"""Ponto de entrada da aplicação: cria a instância FastAPI e monta rotas."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.database import Base, engine
from app.links.router import router as links_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Encurtador de Links")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(links_router)

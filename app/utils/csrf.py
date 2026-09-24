"""Proteção CSRF para formulários renderizados no servidor."""

import secrets

from fastapi import HTTPException, Request, status


def get_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def validate_csrf(request: Request, submitted_token: str) -> None:
    expected = request.session.get("csrf_token")
    try:
        valid = isinstance(expected, str) and secrets.compare_digest(
            expected.encode("ascii"), submitted_token.encode("ascii")
        )
    except UnicodeEncodeError:
        valid = False
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token CSRF inválido.",
        )

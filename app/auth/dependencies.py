"""Dependencies de sessão autenticada."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.repository import UserRepository
from app.database.database import get_db
from app.database.models import User


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    return UserRepository(db).get_by_id(user_id)


def require_user(
    request: Request,
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    if user is None:
        path = request.url.path
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"/login?next={path}"},
        )
    return user

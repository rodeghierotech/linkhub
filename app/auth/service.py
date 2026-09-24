"""Regras de cadastro e autenticação."""

import re

from pwdlib import PasswordHash
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.repository import UserRepository
from app.auth.schemas import RegistrationData
from app.database.models import User

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
password_hash = PasswordHash.recommended()


class AuthError(ValueError):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = UserRepository(db)

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    def register(self, data: RegistrationData) -> User:
        name = data.name.strip()
        email = self.normalize_email(data.email)
        if len(name) < 2:
            raise AuthError("Informe um nome válido.")
        if not EMAIL_PATTERN.fullmatch(email):
            raise AuthError("Informe um e-mail válido.")
        if len(data.password) < 8:
            raise AuthError("A senha deve ter pelo menos 8 caracteres.")
        if data.password != data.password_confirmation:
            raise AuthError("As senhas não coincidem.")
        if self.repository.get_by_email(email):
            raise AuthError("Este e-mail já está em uso.")

        first_user = self.repository.count() == 0
        try:
            user = self.repository.create(
                name=name,
                email=email,
                password_hash=password_hash.hash(data.password),
            )
            if first_user:
                self.repository.claim_legacy_links(user.id)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise AuthError("Este e-mail já está em uso.") from exc
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.repository.get_by_email(self.normalize_email(email))
        if user is None or not password_hash.verify(password, user.password_hash):
            return None
        return user

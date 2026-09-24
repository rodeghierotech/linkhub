"""Valores de entrada da autenticação."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistrationData:
    name: str
    email: str
    password: str
    password_confirmation: str

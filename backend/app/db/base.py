"""Declarative base with an explicit constraint naming convention.

Migrations name every constraint and index explicitly with the same convention, so autogenerate
comparisons stay empty and nothing depends on a PostgreSQL version-specific default (plan §2.11).
"""

from typing import Final

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION: Final = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    # No referred-table suffix: PostgreSQL truncates identifiers at 63 characters.
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

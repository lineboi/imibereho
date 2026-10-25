"""Identifier names fit PostgreSQL's 63-character limit and match between models and migrations.

Regression: an FK name of 64 characters (`fk_<table>_<column>_<referred table>`) made the first real
`upgrade head` fail with IdentifierError. These checks need no database.
"""

import re
from pathlib import Path

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, UniqueConstraint

import app.models  # noqa: F401
from app.db.base import Base

PG_MAX_IDENTIFIER = 63
VERSIONS = Path(__file__).resolve().parents[2] / "alembic" / "versions"
MIGRATION_TEXT = "".join(p.read_text(encoding="utf-8") for p in sorted(VERSIONS.glob("*.py")))
LITERAL_NAMES = set(re.findall(r'"((?:pk|fk|ck|uq|ix)_[a-z0-9_]+)"', MIGRATION_TEXT))


def migration_names() -> set[str]:
    """Literal names, plus the templated helper in 0005 (`fk_{table}_methodology_version`)."""
    names = set(LITERAL_NAMES)
    if 'f"fk_{table}_methodology_version"' in MIGRATION_TEXT:
        names |= {f"fk_{table}_methodology_version" for table in Base.metadata.tables}
    for table, check_name in re.findall(r'\("(\w+)", "(\w+)", "[^"]*"\)', MIGRATION_TEXT):
        names |= {f"pk_{table}", f"ck_{table}_{check_name}"}
    return names


def model_names() -> dict[str, list[str]]:
    kinds: dict[str, list[str]] = {"fk": [], "ck": [], "uq": [], "ix": [], "pk": []}
    for table in Base.metadata.tables.values():
        kinds["pk"].append(str(table.primary_key.name))
        for constraint in table.constraints:
            if isinstance(constraint, ForeignKeyConstraint):
                kinds["fk"].append(str(constraint.name))
            elif isinstance(constraint, CheckConstraint):
                kinds["ck"].append(str(constraint.name))
            elif isinstance(constraint, UniqueConstraint):
                kinds["uq"].append(str(constraint.name))
        kinds["ix"].extend(str(index.name) for index in table.indexes if isinstance(index, Index))
    return kinds


def test_every_model_identifier_fits_postgresql() -> None:
    too_long = [n for names in model_names().values() for n in names if len(n) > PG_MAX_IDENTIFIER]
    assert not too_long, too_long


def test_every_migration_identifier_fits_postgresql() -> None:
    too_long = [n for n in migration_names() if len(n) > PG_MAX_IDENTIFIER]
    assert not too_long, too_long


@pytest.mark.parametrize("kind", ["fk", "ck", "uq", "ix", "pk"])
def test_model_names_are_created_by_the_migrations(kind: str) -> None:
    missing = sorted(set(model_names()[kind]) - migration_names())
    assert not missing, missing


def test_new_revisions_wrap_constraint_names_in_op_f() -> None:
    """After 0006, a bare `name="..."` lets Alembic apply the naming convention a second time
    (the CHECK-constraint defect that 0006 repairs). Revisions 0001-0006 are frozen history."""
    offenders = []
    for path in sorted(VERSIONS.glob("*.py")):
        number = path.name.split("_", 1)[0]
        if not number.isdigit() or int(number) <= 6:
            continue
        for match in re.finditer(r'name=(?!op\.f\()["f]', path.read_text(encoding="utf-8")):
            offenders.append(f"{path.name}: offset {match.start()}")
    assert not offenders, offenders

"""Migration and seed entry points refuse unsafe or incomplete configuration before connecting."""

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.db import migrate, seed

BACKEND = Path(__file__).resolve().parents[2]
VARIABLES = ("ENVIRONMENT", "DATABASE_URL", "TEST_DATABASE_URL", "MIGRATIONS_DATABASE_URL")


@pytest.fixture
def environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[pytest.MonkeyPatch]:
    """A controlled environment. Blank values override anything in backend/.env."""
    for name in VARIABLES:
        monkeypatch.setenv(name, "")
    get_settings.cache_clear()
    yield monkeypatch
    get_settings.cache_clear()


def test_migrate_refuses_without_the_target_variable(
    environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    environment.setenv("ENVIRONMENT", "local")
    assert migrate.main(["--target", "migrations", "upgrade", "head"]) == migrate.EXIT_REFUSED
    assert "MIGRATIONS_DATABASE_URL is not set" in capsys.readouterr().err


def test_migrate_refuses_without_environment(
    environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert migrate.main(["--target", "dev", "current"]) == migrate.EXIT_REFUSED
    assert "ENVIRONMENT: is not set" in capsys.readouterr().err


def test_migrate_refuses_a_downgrade_on_dev(
    environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    environment.setenv("ENVIRONMENT", "local")
    environment.setenv("DATABASE_URL", "postgresql://imibereho:pw@localhost:5432/imibereho")
    assert migrate.main(["--target", "dev", "downgrade", "-1"]) == migrate.EXIT_REFUSED
    err = capsys.readouterr().err
    assert "command_not_allowed" in err and "pw@" not in err


def test_migrate_refuses_the_dev_database_as_the_migrations_target(
    environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    environment.setenv("ENVIRONMENT", "local")
    environment.setenv(
        "MIGRATIONS_DATABASE_URL", "postgresql://imibereho:pw@localhost:5432/imibereho"
    )
    assert migrate.main(["--target", "migrations", "downgrade", "base"]) == migrate.EXIT_REFUSED
    assert "wrong_database" in capsys.readouterr().err


def test_seed_refuses_the_postgres_superuser(
    environment: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    environment.setenv("ENVIRONMENT", "local")
    environment.setenv(
        "TEST_DATABASE_URL", "postgresql://postgres:pw@localhost:5432/imibereho_test"
    )
    assert seed.main(["--target", "test"]) == seed.EXIT_REFUSED
    assert "superuser_name" in capsys.readouterr().err


def test_seed_cannot_target_the_migrations_database() -> None:
    with pytest.raises(SystemExit):
        seed.main(["--target", "migrations"])


def test_bare_alembic_refuses_to_run() -> None:
    """`alembic/env.py` exits unless the guarded wrapper supplied the URL and target."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode != 0
    assert "Refusing to run Alembic directly" in result.stderr + result.stdout


def test_head_revision_is_single_and_latest() -> None:
    assert migrate.head_revision() == "0006"


@pytest.mark.parametrize("script", ["migrate.py", "seed.py"])
def test_entry_point_scripts_show_help(script: str) -> None:
    result = subprocess.run(
        [sys.executable, str(BACKEND / "scripts" / script), "--help"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0 and "--target" in result.stdout

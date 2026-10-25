"""`/ready` checks (contract §2): database, migrations, seed.

- database: `SELECT 1` succeeds.
- migrations: the database's Alembic revision equals this build's head revision.
- seed: every dataset registered in this build has a `seed_state` row at its code hash.
A check that cannot run because an earlier one failed is reported as failed.
"""

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.data.registry import Dataset
from app.db.seed import stored_hashes
from app.db.session import Database

logger = logging.getLogger("app.readiness")

CheckStatus = Literal["ok", "failed"]


@dataclass(frozen=True, slots=True)
class Readiness:
    database: CheckStatus
    migrations: CheckStatus
    seed: CheckStatus

    @property
    def ready(self) -> bool:
        return self.database == self.migrations == self.seed == "ok"

    def as_checks(self) -> dict[str, str]:
        return {"database": self.database, "migrations": self.migrations, "seed": self.seed}


def _migrations_ok(session: Session, head: str) -> bool:
    revisions = session.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    return list(revisions) == [head]


def _seed_ok(session: Session, datasets: Sequence[Dataset]) -> bool:
    stored = stored_hashes(session)
    return all(stored.get(dataset.name) == dataset.content_hash for dataset in datasets)


def _run(name: str, check: Callable[[], bool]) -> CheckStatus:
    try:
        return "ok" if check() else "failed"
    except Exception as exc:
        # The exception type only: messages can carry connection details.
        logger.warning("readiness check failed", extra={"target": name})
        logger.debug("readiness check error type: %s", type(exc).__name__)
        return "failed"


def check_readiness(database: Database, head: str, datasets: Sequence[Dataset]) -> Readiness:
    try:
        with database.read_only_session() as session:
            if (
                _run("database", lambda: session.execute(text("SELECT 1")).scalar_one() == 1)
                != "ok"
            ):
                return Readiness("failed", "failed", "failed")
            migrations = _run("migrations", lambda: _migrations_ok(session, head))
            if migrations != "ok":
                return Readiness("ok", "failed", "failed")
            return Readiness("ok", "ok", _run("seed", lambda: _seed_ok(session, datasets)))
    except Exception:
        logger.warning("readiness check failed", extra={"target": "database"})
        return Readiness("failed", "failed", "failed")

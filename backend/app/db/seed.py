"""Deterministic, idempotent seed framework (plan A3). With migrations, the only database writer.

    uv run python -m app.db.seed --target <dev|test|production> [--check]

- One transaction per run, under `pg_advisory_xact_lock`.
- A dataset whose stored hash equals its code hash is skipped, so a rerun with nothing changed
  commits nothing.
- Version-scoped tables: rows for the current methodology version are deleted (children first),
  then the full set is inserted. Global tables: upsert, then delete rows absent from the set.
  A delete blocked by a foreign key aborts the whole run.
- `seed_state` is updated in the same transaction.
- `--check` recomputes each hash from the table contents (not from `seed_state`).
"""

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal

from sqlalchemy import ColumnElement, Table, delete, select, text, tuple_
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.config import InvalidSettingsError, MissingSettingError, Target, get_settings
from app.core.constants import METHODOLOGY_VERSION
from app.data import DATASETS
from app.data.registry import Dataset, TableRows, content_hash
from app.db.guards import SEED_COMMAND, UnsafeDatabaseTargetError, describe_url
from app.db.session import Database, create_guarded_engine
from app.models import SeedState

ADVISORY_LOCK_KEY: Final = 0x1D1BE7E0  # arbitrary, fixed: "imibereho seed"
SEED_TARGETS: Final = ("dev", "test", "production")
EXIT_REFUSED: Final = 2
EXIT_CHECK_FAILED: Final = 1


@dataclass(frozen=True, slots=True)
class SeedOutcome:
    dataset: str
    action: Literal["applied", "skipped"]


def _scope_filter(part: TableRows) -> tuple[ColumnElement[bool], ...]:
    if part.scope_column is None:
        return ()
    return (part.table.c[part.scope_column] == METHODOLOGY_VERSION,)


def _primary_key(table: Table) -> list[str]:
    return [column.name for column in table.primary_key.columns]


def _delete_version_rows(session: Session, dataset: Dataset) -> None:
    for part in reversed(dataset.tables):  # children first
        if part.scope_column is not None:
            session.execute(delete(part.table).where(*_scope_filter(part)))


def _sync_global_rows(session: Session, part: TableRows) -> None:
    pk = _primary_key(part.table)
    if part.rows:
        statement = insert(part.table).values([dict(row) for row in part.rows])
        update_columns = {name: statement.excluded[name] for name in part.columns if name not in pk}
        session.execute(statement.on_conflict_do_update(index_elements=pk, set_=update_columns))
    keys = [tuple(row[name] for name in pk) for row in part.rows]
    pk_columns = [part.table.c[name] for name in pk]
    stale = delete(part.table)
    if keys:
        stale = stale.where(tuple_(*pk_columns).not_in(keys))
    session.execute(stale)


def _insert(session: Session, dataset: Dataset) -> None:
    for part in dataset.tables:  # parents first
        if part.scope_column is None:
            _sync_global_rows(session, part)
        elif part.rows:
            session.execute(insert(part.table), [dict(row) for row in part.rows])
    statement = insert(SeedState).values(
        dataset=dataset.name,
        methodology_version=METHODOLOGY_VERSION,
        content_hash=dataset.content_hash,
    )
    session.execute(
        statement.on_conflict_do_update(
            index_elements=["dataset"],
            set_={
                "methodology_version": statement.excluded.methodology_version,
                "content_hash": statement.excluded.content_hash,
                "applied_at": text("now()"),
            },
        )
    )


def stored_hashes(session: Session) -> dict[str, str]:
    rows = session.execute(select(SeedState.dataset, SeedState.content_hash)).all()
    return {dataset: hash_ for dataset, hash_ in rows}


def seed(database: Database, datasets: Sequence[Dataset] = DATASETS) -> list[SeedOutcome]:
    """Load every dataset whose stored hash differs, in one transaction."""
    with database.session() as session, session.begin():
        session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": ADVISORY_LOCK_KEY})
        stored = stored_hashes(session)
        pending = [d for d in datasets if stored.get(d.name) != d.content_hash]
        # Two phases, so a parent dataset can be replaced while a later (child) dataset is also
        # pending: delete every pending dataset's version rows children-first, then insert
        # parents-first. Rows still referenced by a dataset that is *not* pending make the
        # delete fail, which aborts the whole run.
        for dataset in reversed(pending):
            _delete_version_rows(session, dataset)
        for dataset in pending:
            _insert(session, dataset)
        outcomes = [SeedOutcome(d.name, "applied" if d in pending else "skipped") for d in datasets]
    return outcomes


def table_hash(session: Session, dataset: Dataset) -> str:
    """Recompute a dataset's hash from what is actually in the tables."""
    parts = []
    for part in dataset.tables:
        columns = [part.table.c[name] for name in part.columns]
        rows = session.execute(select(*columns).where(*_scope_filter(part))).mappings().all()
        parts.append((part.table.name, [dict(row) for row in rows]))
    return content_hash(parts)


def check(database: Database, datasets: Sequence[Dataset] = DATASETS) -> list[str]:
    """Return the names of datasets whose table contents do not match the code."""
    with database.read_only_session() as session:
        return [d.name for d in datasets if table_hash(session, d) != d.content_hash]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.db.seed", description=__doc__)
    parser.add_argument("--target", required=True, choices=SEED_TARGETS)
    parser.add_argument("--check", action="store_true", help="verify table contents only")
    parsed = parser.parse_args(argv)
    target: Target = parsed.target
    try:
        settings = get_settings()
        url = settings.database_url_for(target)
        engine = create_guarded_engine(
            url,
            target,
            settings.environment,
            SEED_COMMAND,
            allow_local_superuser=settings.allow_local_superuser,
        )
    except (InvalidSettingsError, MissingSettingError, UnsafeDatabaseTargetError) as exc:
        print(f"[seed] refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    database = Database(engine, target)
    print(f"[seed] target={target} database={describe_url(url)}")
    try:
        if parsed.check:
            mismatched = check(database)
            for name in mismatched:
                print(f"[seed] MISMATCH {name}", file=sys.stderr)
            print(f"[seed] check: {len(DATASETS) - len(mismatched)}/{len(DATASETS)} datasets match")
            return EXIT_CHECK_FAILED if mismatched else 0
        for outcome in seed(database):
            print(f"[seed] {outcome.action:<8} {outcome.dataset}")
        return 0
    except UnsafeDatabaseTargetError as exc:
        print(f"[seed] refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    finally:
        database.dispose()


if __name__ == "__main__":
    raise SystemExit(main())

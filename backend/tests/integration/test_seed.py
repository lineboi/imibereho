"""Seed framework on `imibereho_test`: idempotent, deterministic, all-or-nothing, drift-detecting.

Each test leaves the database exactly as seeded (verified by `check`).
"""

from collections.abc import Iterator

import pytest
from sqlalchemy import delete, func, insert, select, text
from sqlalchemy.exc import IntegrityError

from app.data import DATASETS
from app.data.registry import Dataset, TableRows
from app.db.seed import check, seed, stored_hashes, table_hash
from app.db.session import Database
from app.models import District, SeasonalTip, SeedState, SyntheticHousehold

BY_NAME = {dataset.name: dataset for dataset in DATASETS}


@pytest.fixture
def seeded(test_database: Database) -> Iterator[Database]:
    yield test_database
    # Restore: force every dataset to reapply, then prove the tables match the code.
    with test_database.session() as session, session.begin():
        session.execute(delete(SeedState))
    seed(test_database)
    assert check(test_database) == []


def test_full_reseed_replaces_parents_and_children_together(seeded: Database) -> None:
    """Every dataset pending at once (parents with dependants) must succeed, not hit an FK."""
    with seeded.session() as session, session.begin():
        session.execute(delete(SeedState))
    assert {o.action for o in seed(seeded)} == {"applied"}
    assert check(seeded) == []


def test_second_run_is_a_no_op(seeded: Database) -> None:
    outcomes = seed(seeded)
    assert {o.action for o in outcomes} == {"skipped"}
    assert [o.dataset for o in outcomes] == [d.name for d in DATASETS]


def test_stored_hashes_match_the_code(seeded: Database) -> None:
    with seeded.read_only_session() as session:
        assert stored_hashes(session) == {d.name: d.content_hash for d in DATASETS}


def test_check_recomputes_from_table_contents_and_detects_drift(seeded: Database) -> None:
    with seeded.session() as session, session.begin():
        session.execute(insert(District).values(code="atlantis", name="Atlantis", sort_order=99))
    assert check(seeded) == ["districts"]  # seed_state still says "ok"; the table does not


def test_reapplying_a_global_dataset_removes_stale_rows(seeded: Database) -> None:
    with seeded.session() as session, session.begin():
        session.execute(insert(District).values(code="atlantis", name="Atlantis", sort_order=99))
        session.execute(delete(SeedState).where(SeedState.dataset == "districts"))
    outcomes = {o.dataset: o.action for o in seed(seeded)}
    assert outcomes["districts"] == "applied"
    assert outcomes["synthetic_households"] == "skipped"
    with seeded.read_only_session() as session:
        assert session.get(District, "atlantis") is None
        assert session.scalar(select(func.count()).select_from(District)) == 30


def test_reapplying_a_version_scoped_dataset_replaces_its_rows(seeded: Database) -> None:
    with seeded.session() as session, session.begin():
        session.execute(text("UPDATE synthetic_households SET savings = 0 WHERE id = 1"))
        session.execute(delete(SeedState).where(SeedState.dataset == "synthetic_households"))
    seed(seeded)
    with seeded.read_only_session() as session:
        assert (
            table_hash(session, BY_NAME["synthetic_households"])
            == BY_NAME["synthetic_households"].content_hash
        )
        assert session.scalar(select(func.count()).select_from(SyntheticHousehold)) == 3_000


def test_a_failure_rolls_the_whole_run_back(seeded: Database) -> None:
    renamed = Dataset(
        "districts",
        lambda: (
            TableRows(
                District,
                None,
                tuple(
                    {**row, "name": f"Changed {row['name']}"}
                    for row in BY_NAME["districts"].tables[0].rows
                ),
            ),
        ),
    )

    # Its phase-1 delete removes the real tip, then its insert violates CHECK (month 1-12),
    # after the renamed districts were written.
    bad_tip = {**BY_NAME["seasonal"].tables[1].rows[0], "id": "bad", "month": 13}
    violates_check = Dataset(
        "bad_tips", lambda: (TableRows(SeasonalTip, "methodology_version", (bad_tip,)),)
    )

    with pytest.raises(IntegrityError):
        seed(seeded, [renamed, violates_check])
    assert check(seeded) == []  # renamed districts and the deleted tip were both rolled back
    with seeded.read_only_session() as session:
        gasabo = session.get(District, "gasabo")
        assert gasabo is not None and gasabo.name == "Gasabo"
        assert session.scalar(select(func.count()).select_from(SeasonalTip)) == 1
        assert "bad_tips" not in stored_hashes(session)


def test_hashes_are_stable_across_runs() -> None:
    first = [d.content_hash for d in DATASETS]
    rebuilt = [Dataset(d.name, d.build).content_hash for d in DATASETS]
    assert first == rebuilt

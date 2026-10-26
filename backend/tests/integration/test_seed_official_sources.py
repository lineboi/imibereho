"""Official sources sharing `statistical_sources` (FinScope 2024 and EICV7) on `imibereho_test`.

Each dataset owns only its own source's rows. Reseeding one must not delete, change or re-hash
the other; rows no dataset owns are still removed and detected, as before partitioning.
Each test leaves the database exactly as seeded (verified by `check`).
"""

from collections.abc import Iterator
from typing import Any, Final, cast

import pytest
from sqlalchemy import Table, delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.data import DATASETS
from app.data.registry import Dataset, TableRows
from app.db.seed import check, seed, stored_hashes, table_hash
from app.db.session import Database
from app.models import (
    FinancialAccessStrandDistrict,
    FinancialInclusionIndicator,
    SeedState,
    StatisticalSource,
    SurveyEstimate,
)

BY_NAME: Final = {dataset.name: dataset for dataset in DATASETS}
FINSCOPE: Final = ("finscope_2024", "finscope-2024")
EICV7: Final = ("eicv7_2023_24", "eicv7-2023-2024")
SOURCE_TABLES: Final = {
    "finscope-2024": (FinancialInclusionIndicator, FinancialAccessStrandDistrict),
    "eicv7-2023-2024": (SurveyEstimate,),
}


@pytest.fixture
def seeded(test_database: Database) -> Iterator[Database]:
    yield test_database
    with test_database.session() as session, session.begin():
        session.execute(delete(SeedState))
    seed(test_database)
    assert check(test_database) == []


def snapshot(session: Session, source_id: str, tables_of: str | None = None) -> dict[str, Any]:
    """Every row a source owns, column by column, plus its source record. `tables_of` names
    the registered source whose child tables to read (for a source ID that is not registered).
    """
    rows: dict[str, Any] = {}
    source = session.execute(
        select(StatisticalSource.__table__).where(StatisticalSource.id == source_id)
    ).mappings()
    rows["statistical_sources"] = [dict(r) for r in source]
    for model in SOURCE_TABLES[tables_of or source_id]:
        table = cast(Table, model.__table__)
        result = session.execute(select(table).where(table.c.source_id == source_id)).mappings()
        rows[table.name] = sorted((dict(r) for r in result), key=repr)
    return rows


def forget(database: Database, dataset: str) -> None:
    with database.session() as session, session.begin():
        session.execute(delete(SeedState).where(SeedState.dataset == dataset))


def test_both_sources_coexist_with_their_own_attribution(seeded: Database) -> None:
    with seeded.read_only_session() as session:
        rows = session.execute(select(StatisticalSource.id, StatisticalSource.publisher)).all()
        publishers = {source_id: publisher for source_id, publisher in rows}
        assert publishers == {
            "finscope-2024": "Access to Finance Rwanda (AFR)",
            "eicv7-2023-2024": "National Institute of Statistics of Rwanda (NISR)",
        }
        finscope, eicv7 = snapshot(session, "finscope-2024"), snapshot(session, "eicv7-2023-2024")
        assert len(finscope["financial_inclusion_indicators"]) == 11
        assert len(finscope["financial_access_strand_districts"]) == 30
        assert len(eicv7["survey_estimates"]) == 83
        for name in (FINSCOPE[0], EICV7[0]):
            assert table_hash(session, BY_NAME[name]) == BY_NAME[name].content_hash
        assert {name: stored_hashes(session)[name] for name in (FINSCOPE[0], EICV7[0])} == {
            name: BY_NAME[name].content_hash for name in (FINSCOPE[0], EICV7[0])
        }


@pytest.mark.parametrize(("changed", "other"), [(EICV7, FINSCOPE), (FINSCOPE, EICV7)])
def test_reseeding_one_source_leaves_the_other_untouched(
    seeded: Database, changed: tuple[str, str], other: tuple[str, str]
) -> None:
    # Damage the changed source's record so the reseed really rewrites it.
    with seeded.session() as session, session.begin():
        session.execute(
            update(StatisticalSource).where(StatisticalSource.id == changed[1]).values(notes="x")
        )
    forget(seeded, changed[0])
    with seeded.read_only_session() as session:
        before = snapshot(session, other[1])
    outcomes = {o.dataset: o.action for o in seed(seeded)}
    assert outcomes[changed[0]] == "applied" and outcomes[other[0]] == "skipped"
    with seeded.read_only_session() as session:
        assert snapshot(session, other[1]) == before
        assert table_hash(session, BY_NAME[other[0]]) == BY_NAME[other[0]].content_hash
        restored = session.get(StatisticalSource, changed[1])
        assert restored is not None and restored.notes != "x"
    assert check(seeded) == []
    assert {o.action for o in seed(seeded)} == {"skipped"}  # idempotent again


def test_seeding_only_one_dataset_never_removes_the_other(seeded: Database) -> None:
    forget(seeded, EICV7[0])
    with seeded.read_only_session() as session:
        before = snapshot(session, FINSCOPE[1])
    assert [o.action for o in seed(seeded, [BY_NAME[EICV7[0]]])] == ["applied"]
    with seeded.read_only_session() as session:
        assert snapshot(session, FINSCOPE[1]) == before
    assert check(seeded) == []


def _extra_estimate(source_id: str, code: str) -> dict[str, object]:
    row = dict(BY_NAME[EICV7[0]].tables[1].rows[0])
    return {**row, "source_id": source_id, "category_code": code, "sort_order": 9999}


def test_stale_rows_are_removed_only_inside_the_reseeded_partition(seeded: Database) -> None:
    finscope_row = {**BY_NAME[FINSCOPE[0]].tables[1].rows[0], "code": "stray_indicator"}
    with seeded.session() as session, session.begin():
        session.execute(insert(SurveyEstimate).values(_extra_estimate(EICV7[1], "stray")))
        session.execute(insert(FinancialInclusionIndicator).values(finscope_row))
    assert check(seeded) == [FINSCOPE[0], EICV7[0]]  # both drifts detected
    forget(seeded, EICV7[0])
    seed(seeded)  # FinScope's hash still matches seed_state, so only EICV7 is reapplied
    with seeded.read_only_session() as session:
        assert session.get(SurveyEstimate, (EICV7[1], "A9.23", "poverty_headcount_rate",
                                            "national", "stray")) is None  # fmt: skip
        assert session.get(FinancialInclusionIndicator, (FINSCOPE[1], "stray_indicator"))
    assert check(seeded) == [FINSCOPE[0]]  # left for FinScope's own reseed (the fixture's)


def test_a_source_no_dataset_owns_is_detected_and_removed(seeded: Database) -> None:
    unknown = {**dict(BY_NAME[EICV7[0]].tables[0].rows[0]), "id": "unregistered-source"}
    with seeded.session() as session, session.begin():
        session.execute(insert(StatisticalSource).values(unknown))
        session.execute(
            insert(SurveyEstimate).values(_extra_estimate("unregistered-source", "rwanda"))
        )
    # Every dataset using a table that holds the row is reported, as for a global table.
    assert check(seeded) == [FINSCOPE[0], EICV7[0]]
    forget(seeded, EICV7[0])
    seed(seeded)  # children are removed before their unowned source: no FK error
    with seeded.read_only_session() as session:
        assert session.get(StatisticalSource, "unregistered-source") is None
        assert not session.scalars(
            select(SurveyEstimate).where(SurveyEstimate.source_id == "unregistered-source")
        ).all()
    assert check(seeded) == []


def test_a_failed_reseed_rolls_back_and_keeps_both_sources(seeded: Database) -> None:
    good = BY_NAME[EICV7[0]]
    bad_rows = (
        {**good.tables[1].rows[0], "estimate_pct": 101},  # violates CHECK estimate_pct_range
        *good.tables[1].rows[1:],
    )
    broken = Dataset(
        EICV7[0],
        lambda: (
            good.tables[0],
            TableRows(SurveyEstimate, None, bad_rows, partition=("source_id", EICV7[1])),
        ),
    )
    with seeded.read_only_session() as session:
        before = {sid: snapshot(session, sid) for sid in (FINSCOPE[1], EICV7[1])}
    with pytest.raises(IntegrityError):
        seed(seeded, [broken])
    with seeded.read_only_session() as session:
        assert {sid: snapshot(session, sid) for sid in (FINSCOPE[1], EICV7[1])} == before
        assert stored_hashes(session)[EICV7[0]] == good.content_hash
    assert check(seeded) == []


def test_unowned_rows_in_another_sources_tables_never_block_a_reseed(seeded: Database) -> None:
    """A stray source whose child sits in a FinScope-only table must not make an EICV7-only
    reseed fail on the foreign key: unowned rows are cleared from every shared table."""
    stray_source = {**dict(BY_NAME[EICV7[0]].tables[0].rows[0]), "id": "unregistered-source"}
    stray_child = {**BY_NAME[FINSCOPE[0]].tables[1].rows[0], "source_id": "unregistered-source"}
    with seeded.session() as session, session.begin():
        session.execute(insert(StatisticalSource).values(stray_source))
        session.execute(insert(FinancialInclusionIndicator).values(stray_child))
    with seeded.read_only_session() as session:
        before = {sid: snapshot(session, sid) for sid in (FINSCOPE[1], EICV7[1])}
    forget(seeded, EICV7[0])
    outcomes = {o.dataset: o.action for o in seed(seeded)}
    assert outcomes[EICV7[0]] == "applied" and outcomes[FINSCOPE[0]] == "skipped"
    with seeded.read_only_session() as session:
        assert session.get(StatisticalSource, "unregistered-source") is None
        assert (
            session.get(FinancialInclusionIndicator, ("unregistered-source", stray_child["code"]))
            is None
        )
        assert {sid: snapshot(session, sid) for sid in (FINSCOPE[1], EICV7[1])} == before
    assert check(seeded) == []


# --- Permanent regressions from the shared-source review ---

DRIFT: Final = "drifted by test"
# One owned child row per source, to drift: (model, condition picking the row).
CHILD_TO_DRIFT: Final = {
    FINSCOPE[1]: (FinancialInclusionIndicator, FinancialInclusionIndicator.code == "banked"),
    EICV7[1]: (SurveyEstimate, SurveyEstimate.category_code == "huye"),
}


def seed_state_row(session: Session, dataset: str) -> dict[str, Any]:
    table = cast(Table, SeedState.__table__)
    return dict(session.execute(select(table).where(table.c.dataset == dataset)).mappings().one())


@pytest.mark.parametrize(("seeded_alone", "other"), [(EICV7, FINSCOPE), (FINSCOPE, EICV7)])
def test_seeding_one_source_alone_leaves_the_others_rows_exactly_as_they_are(
    seeded: Database, seeded_alone: tuple[str, str], other: tuple[str, str]
) -> None:
    """The other source is drifted first, so any write to it (even a "repair") would show."""
    model, child = CHILD_TO_DRIFT[other[1]]
    table = cast(Table, model.__table__)
    with seeded.session() as session, session.begin():
        session.execute(
            update(StatisticalSource).where(StatisticalSource.id == other[1]).values(notes=DRIFT)
        )
        session.execute(
            update(table).where(table.c.source_id == other[1], child).values(notes=DRIFT)
        )
        # Damage the seeded source too, so its reseed really rewrites rows.
        session.execute(
            update(StatisticalSource)
            .where(StatisticalSource.id == seeded_alone[1])
            .values(notes="x")
        )
    forget(seeded, seeded_alone[0])
    with seeded.read_only_session() as session:
        before = snapshot(session, other[1])
        before_state = seed_state_row(session, other[0])
    assert [o.action for o in seed(seeded, [BY_NAME[seeded_alone[0]]])] == ["applied"]
    with seeded.read_only_session() as session:
        assert snapshot(session, other[1]) == before  # row for row, drift included
        assert seed_state_row(session, other[0]) == before_state  # not re-stamped
        assert (
            table_hash(session, BY_NAME[seeded_alone[0]]) == BY_NAME[seeded_alone[0]].content_hash
        )
    assert check(seeded) == [other[0]]  # the drift is still there, and still detected


def _with_source_id(dataset: Dataset, new_id: str) -> Dataset:
    def build() -> tuple[TableRows, ...]:
        source, *children = dataset.tables
        return (
            TableRows(StatisticalSource, None, ({**source.rows[0], "id": new_id},),
                      partition=("id", new_id)),
            *(
                TableRows(part.model, None,
                          tuple({**row, "source_id": new_id} for row in part.rows),
                          partition=("source_id", new_id))
                for part in children
            ),
        )  # fmt: skip

    return Dataset(dataset.name, build)


@pytest.mark.parametrize(("renamed", "other"), [(EICV7, FINSCOPE), (FINSCOPE, EICV7)])
def test_changing_a_source_id_moves_its_rows_and_leaves_the_other_source_untouched(
    seeded: Database, renamed: tuple[str, str], other: tuple[str, str]
) -> None:
    new_id = f"{renamed[1]}-renamed-by-test"
    with seeded.read_only_session() as session:
        old_rows = snapshot(session, renamed[1])
        other_before = snapshot(session, other[1])
    dataset = _with_source_id(BY_NAME[renamed[0]], new_id)
    # The old ID becomes unowned: its children go first, then its source row (no FK error).
    assert [o.action for o in seed(seeded, [dataset])] == ["applied"]
    with seeded.read_only_session() as session:
        assert snapshot(session, renamed[1]) == {name: [] for name in old_rows}
        moved = snapshot(session, new_id, tables_of=renamed[1])
        assert moved["statistical_sources"] == [
            {**row, "id": new_id} for row in old_rows["statistical_sources"]
        ]
        for name, rows in old_rows.items():
            if name != "statistical_sources":  # every child row, every column, only re-keyed
                expected = sorted(({**row, "source_id": new_id} for row in rows), key=repr)
                assert moved[name] == expected
        assert snapshot(session, other[1]) == other_before
    assert check(seeded, [dataset]) == []
    # Against the real registry the new ID is unowned drift, reported for both sources; the
    # fixture's reseed renames it back and must end at check() == [].
    assert check(seeded) == [FINSCOPE[0], EICV7[0]]


def _emptied(dataset: Dataset) -> Dataset:
    source, *children = dataset.tables
    return Dataset(
        dataset.name,
        lambda: (source, *(TableRows(p.model, None, (), partition=p.partition) for p in children)),
    )


@pytest.mark.parametrize(("emptied", "other"), [(EICV7, FINSCOPE), (FINSCOPE, EICV7)])
def test_an_empty_partition_empties_only_that_source(
    seeded: Database, emptied: tuple[str, str], other: tuple[str, str]
) -> None:
    with seeded.read_only_session() as session:
        source_before = snapshot(session, emptied[1])["statistical_sources"]
        other_before = snapshot(session, other[1])
    dataset = _emptied(BY_NAME[emptied[0]])
    assert [o.action for o in seed(seeded, [dataset])] == ["applied"]
    with seeded.read_only_session() as session:
        after = snapshot(session, emptied[1])
        assert after == {
            "statistical_sources": source_before,  # the source record itself is kept
            **{cast(Table, m.__table__).name: [] for m in SOURCE_TABLES[emptied[1]]},
        }
        assert snapshot(session, other[1]) == other_before
        assert table_hash(session, dataset) == dataset.content_hash
    assert check(seeded, [dataset]) == []
    assert check(seeded) == [emptied[0]]  # only the emptied source differs from the code

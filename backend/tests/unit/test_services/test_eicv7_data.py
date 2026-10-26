"""EICV7 2023/24 transcription: Tables A9.23 (poverty) and A3.7 (health insurance).

Values were extracted from NISR's workbook (SHA-256 8a01ec05…350d) by
`python -m app.data.eicv7_workbook`, which also re-checks every cell. They were cross-checked
against the report's printed two-decimal tables (pp. 91 and 107): 498 of 498 values match. If a
value here changes, re-run that check against the workbook first.
"""

from collections import Counter
from collections.abc import Callable, Mapping
from decimal import ROUND_HALF_UP, Decimal
from typing import Final

import pytest

from app.core.constants import EICV7_SOURCE_ID
from app.data import DATASETS
from app.data.eicv7_2023_24 import (
    HEALTH_INSURANCE,
    POVERTY,
    ROW_NOTES,
    SOURCE,
    TABLES,
    Row,
    category_code,
)
from app.data.reference import DISTRICT_CODES
from app.data.registry import Dataset, TableRows, content_hash, shared_tables
from app.models import StatisticalSource, SurveyEstimate

BY_TABLE: Final = {"A9.23": POVERTY, "A3.7": HEALTH_INSURANCE}
DATASET: Final = next(d for d in DATASETS if d.name == "eicv7_2023_24")
PROVINCES: Final = ["city_of_kigali", "southern", "western", "northern", "eastern"]


def row(table: str, code: str) -> Row:
    return next(r for r in BY_TABLE[table] if r[1] == code)


def values(r: Row) -> list[Decimal | None]:
    return [Decimal(v) if v is not None else None for v in r[3:]]


def estimate_rows() -> tuple[Mapping[str, object], ...]:
    return next(part.rows for part in DATASET.tables if part.model is SurveyEstimate)


# --- Counts and coverage ---


def test_poverty_record_counts_by_dimension() -> None:
    assert len(POVERTY) == 38
    assert Counter(r[0] for r in POVERTY) == {
        "national": 1, "area": 2, "province": 5, "district": 30,
    }  # fmt: skip


def test_health_insurance_record_counts_by_dimension() -> None:
    assert len(HEALTH_INSURANCE) == 45
    assert Counter(r[0] for r in HEALTH_INSURANCE) == {
        "national": 1, "sex": 2, "area": 2, "province": 5, "quintile": 5, "district": 30,
    }  # fmt: skip


@pytest.mark.parametrize("table", ["A9.23", "A3.7"])
def test_every_district_once_and_every_group(table: str) -> None:
    rows = BY_TABLE[table]
    districts = [r[1] for r in rows if r[0] == "district"]
    assert sorted(districts) == sorted(DISTRICT_CODES)
    assert len({(r[0], r[1]) for r in rows}) == len(rows)  # no duplicate group
    assert [r[1] for r in rows if r[0] == "province"] == PROVINCES
    assert [r[1] for r in rows if r[0] == "area"] == ["urban", "rural"]
    assert [r[1] for r in rows if r[0] == "national"] == ["rwanda"]


def test_sex_and_quintile_only_in_health_insurance() -> None:
    assert [r[1] for r in HEALTH_INSURANCE if r[0] == "sex"] == ["male", "female"]
    assert [r[1] for r in HEALTH_INSURANCE if r[0] == "quintile"] == ["q1", "q2", "q3", "q4", "q5"]
    assert not {r[0] for r in POVERTY} & {"sex", "quintile"}


def test_published_order_is_kept() -> None:
    """Rows stay in the workbook's order: sections as printed, districts by province."""
    assert [r[0] for r in HEALTH_INSURANCE][:6] == [
        "national", "sex", "sex", "area", "area", "province",
    ]  # fmt: skip
    districts = [r[1] for r in POVERTY if r[0] == "district"]
    assert districts[:4] == ["nyarugenge", "gasabo", "kicukiro", "nyanza"]
    assert districts[-1] == "bugesera"


def test_labels_are_published_text_and_codes_follow_from_them() -> None:
    for spec in TABLES:
        for dimension, code, label, *_ in BY_TABLE[spec.table_id]:
            assert category_code(dimension, label) == code
    assert row("A9.23", "rwanda")[2] == "Poverty Rate"  # the workbook's own label
    assert row("A3.7", "rwanda")[2] == "Rwanda"
    with pytest.raises(KeyError):
        category_code("district", "Kigali")
    with pytest.raises(KeyError):
        category_code("quintile", "Q6")


# --- Exact values ---


@pytest.mark.parametrize(
    ("table", "code", "expected"),
    [
        ("A9.23", "rwanda", ("27.362976067289672", "0.49624639004466625", "26.389621090104246",
                             "28.336331044475099", "1.8135687756489709", "1.8650754691612403")),
        ("A9.23", "urban", ("16.69437894637872", "0.90542229193848334", "14.918452084253564",
                            "18.470305808503873", "5.4235158722983465", "2.515588670510791")),
        ("A9.23", "western", ("37.412058313592915", "1.1685376959257137", "35.120047721322997",
                              "39.704068905862833", "3.1234253034967314", "1.8828246325074596")),
        ("A9.23", "nyamagabe", ("51.39408818367712", "3.2140169282663194", "45.090003284228963",
                                "57.698173083125276", "6.2536704937341385", "1.6701460450989005")),
        ("A9.23", "nyarugenge", ("6.7999300949706969", "1.2026866468360777",
                                 "4.4409385593607729", "9.1589216305806218", "17.68675015829351",
                                 "0.99491109990941295")),
        ("A3.7", "rwanda", ("85.310917075321285", "0.36316526070014143", "84.598592066747401",
                            "86.02324208389517", "0.42569611621863312", "6.531306740603827")),
        ("A3.7", "female", ("85.677015852419231", "0.38309664468282439", "84.925596732148151",
                            "86.428434972690312", "0.44714050888830886", "3.8714253927839133")),
        ("A3.7", "q1", ("76.018949867683503", "0.93849125667523137", "74.178160384766315",
                        "77.859739350600691", "1.2345490937572059", "5.9935137246573733")),
        ("A3.7", "gakenke", ("96.349709583879303", "0.77734109800031914", "94.825005642675237",
                             "97.874413525083369", "0.80679132439271994", "2.9391623308704036")),
        ("A3.7", "gasabo", ("86.25335754912301", "1.7964095232332549", "82.729817256275723",
                            "89.776897841970296", "2.0827125740701327", "12.100523037825447")),
    ],
)  # fmt: skip
def test_anchor_values_exactly_as_stored_in_the_workbook(
    table: str, code: str, expected: tuple[str, ...]
) -> None:
    assert row(table, code)[3:] == expected
    assert values(row(table, code)) == [Decimal(v) for v in expected]


@pytest.mark.parametrize(
    ("table", "code", "printed"),
    [
        ("A9.23", "rwanda", ("27.36", "0.50", "26.39", "28.34", "1.81", "1.87")),  # p. 107
        ("A9.23", "gisagara", ("45.59", "2.69", "40.32", "50.86", "5.89", "1.29")),
        ("A9.23", "kicukiro", ("6.93", "1.34", "4.30", "9.55", "19.31", "1.53")),
        ("A3.7", "rwanda", ("85.31", "0.36", "84.60", "86.02", "0.43", "6.53")),  # p. 91
        ("A3.7", "northern", ("91.67", "0.66", "90.38", "92.97", "0.72", "5.48")),
        ("A3.7", "q5", ("93.38", "0.44", "92.51", "94.24", "0.47", "3.92")),
        ("A3.7", "rusizi", ("78.09", "2.52", "73.16", "83.03", "3.22", "8.50")),
    ],
)
def test_values_round_to_the_printed_report(
    table: str, code: str, printed: tuple[str, ...]
) -> None:
    rounded = [v.quantize(Decimal("0.01"), ROUND_HALF_UP) for v in values(row(table, code)) if v]
    assert rounded == [Decimal(p) for p in printed]


def test_headline_figures_from_the_report_text() -> None:
    """27.4% poor (p. 17); 85.3% insured (p. 15); Northern 92% (p. 15)."""

    def one_decimal(value: str) -> Decimal:
        return Decimal(value).quantize(Decimal("0.1"), ROUND_HALF_UP)

    assert one_decimal(row("A9.23", "rwanda")[3]) == Decimal("27.4")
    assert one_decimal(row("A9.23", "urban")[3]) == Decimal("16.7")
    assert one_decimal(row("A9.23", "rural")[3]) == Decimal("31.6")
    assert one_decimal(row("A3.7", "rwanda")[3]) == Decimal("85.3")
    assert round(Decimal(row("A3.7", "northern")[3])) == 92


def test_full_precision_is_kept_and_is_exactly_the_workbook_double() -> None:
    """Text is stored verbatim (no float). Each value is the 17-digit form of an IEEE double, so
    the API's JSON number parses back to exactly the cell's value."""
    for table in BY_TABLE.values():
        for r in table:
            for text in r[3:]:
                assert text is not None
                assert str(Decimal(text)) == text  # no exponent, no reformatting
                assert Decimal(text) == Decimal(format(float(text), ".17g"))
    for stored in estimate_rows():
        assert isinstance(stored["estimate_pct"], Decimal)
        assert all(
            isinstance(stored[name], Decimal | None)
            for name in ("standard_error_pct", "ci_lower_pct", "ci_upper_pct", "cv_pct")
        )


# --- Invariants ---


def test_no_blank_cells_in_either_table() -> None:
    """Both tables publish all six values for every record, so nothing is null."""
    assert all(v is not None for table in BY_TABLE.values() for r in table for v in r[3:])


def test_ranges_and_confidence_interval_order() -> None:
    for table in BY_TABLE.values():
        for r in table:
            estimate, se, lower, upper, cv, deff = values(r)
            assert estimate is not None and lower is not None and upper is not None
            assert Decimal(0) <= lower <= estimate <= upper <= Decimal(100), r[1]
            assert se is not None and se >= 0
            assert cv is not None and cv >= 0
            assert deff is not None and deff > 0


def test_published_uncertainty_is_internally_consistent() -> None:
    """A consistency check only; nothing is recomputed or served from this. Every published CI
    is centred on its estimate with half-width 1.9614 standard errors, and CV = 100 SE / estimate.
    """
    for table in BY_TABLE.values():
        for r in table:
            estimate, se, lower, upper, cv, _ = values(r)
            assert estimate and se and lower and upper and cv
            assert abs((lower + upper) / 2 - estimate) < Decimal("1e-12")
            assert Decimal("1.9614") < (upper - lower) / 2 / se < Decimal("1.9615")
            assert abs(se / estimate * 100 - cv) < Decimal("1e-12")


# --- Seed rows, provenance and notes ---


def test_seed_rows_carry_table_indicator_and_citation() -> None:
    rows = estimate_rows()
    assert len(rows) == 83
    by_table = Counter((r["table_id"], r["indicator_code"], r["page"]) for r in rows)
    assert by_table == {
        ("A9.23", "poverty_headcount_rate", 107): 38,
        ("A3.7", "health_insurance_coverage", 91): 45,
    }
    assert {r["source_id"] for r in rows} == {EICV7_SOURCE_ID}
    assert {r["unit"] for r in rows} == {"percent"}
    assert {r["survey_round"] for r in rows} == {"2023/24"}
    assert {r["printed_decimals"] for r in rows} == {2}
    assert len({r["sort_order"] for r in rows}) == 83
    for r in rows:
        assert (r["district_code"] is not None) == (r["dimension"] == "district")
        assert str(r["table_or_figure"]).startswith(f"Table {r['table_id']}:")


def test_row_notes_are_attached_where_the_source_disagrees_with_itself() -> None:
    notes = {(r["table_id"], r["category_code"]): r["notes"] for r in estimate_rows()}
    assert {key for key, note in notes.items() if note} == set(ROW_NOTES)
    assert "46.6%" in str(notes[("A9.23", "gisagara")])
    assert "'Rwanda'" in str(notes[("A9.23", "rwanda")])


def test_source_provenance() -> None:
    assert SOURCE["id"] == EICV7_SOURCE_ID == "eicv7-2023-2024"
    assert SOURCE["publisher"] == "National Institute of Statistics of Rwanda (NISR)"
    assert str(SOURCE["citation"]).startswith("National Institute of Statistics of Rwanda (NISR) "
                                              "(2025) Seventh Integrated Household")  # fmt: skip
    assert SOURCE["fieldwork_period"] == (
        "October 2023 - October 2024 (12 months in nine cycles; pp. 11, 12, 15)"
    )
    assert SOURCE["survey_round"] == "2023/24"
    assert SOURCE["sample_size"] == 15_054
    assert SOURCE["lowest_published_geography"] == "district"
    assert SOURCE["document_sha256"] == (
        "8a01ec05d851d9813a855e513eb0e74046a070ca0235df9e81730560028e350d"
    )
    assert str(SOURCE["document_url"]).startswith("https://statistics.gov.rw/")
    assert "Access to Finance" not in str(SOURCE)  # not the FinScope publisher


def test_methodology_notes_state_the_poverty_line_and_comparability() -> None:
    notes = str(SOURCE["notes"])
    for phrase in (
        "RWF 560,127 per adult equivalent per year in January 2024 prices",
        "RWF 356,432",
        "not directly comparable",
        "modelled 2016/17 rate of 39.8%",
        "27.4% in 2023/24",
        "12.4 percentage points",
        "38.2%",
        "15,054 households (62,110 people)",
    ):
        assert phrase in notes, phrase


# --- Registration and hashing ---


def test_registered_after_districts_and_finscope() -> None:
    names = [d.name for d in DATASETS]
    assert names.index("districts") < names.index("finscope_2024") < names.index("eicv7_2023_24")


def test_each_official_dataset_owns_only_its_partition() -> None:
    for name, source_id in (("eicv7_2023_24", EICV7_SOURCE_ID), ("finscope_2024", "finscope-2024")):
        dataset = next(d for d in DATASETS if d.name == name)
        for part in dataset.tables:
            assert part.partition is not None
            column, value = part.partition
            assert value == source_id
            assert {r[column] for r in part.rows} == {source_id}


def test_partition_does_not_change_the_content_hash() -> None:
    """So the FinScope dataset's stored hash still matches after it was partitioned."""
    for dataset in DATASETS:
        plain = content_hash((p.table.name, p.rows) for p in dataset.tables)
        assert plain == dataset.content_hash


def test_rows_outside_the_partition_are_refused() -> None:
    bad = Dataset(
        "bad",
        lambda: (
            TableRows(StatisticalSource, None, ({**SOURCE, "id": "other"},), partition=("id", "x")),
        ),
    )
    with pytest.raises(ValueError, match="outside its partition"):
        _ = bad.tables


def test_content_hash_is_stable() -> None:
    assert Dataset(DATASET.name, DATASET.build).content_hash == DATASET.content_hash


def test_shared_tables_list_every_owner_parents_first() -> None:
    shared = shared_tables(DATASETS)
    assert list(shared) == [
        "statistical_sources",
        "financial_inclusion_indicators",
        "financial_access_strand_districts",
        "survey_estimates",
    ]
    sources = shared["statistical_sources"]
    assert sources.column == "id"
    assert sources.owned == {"finscope-2024", EICV7_SOURCE_ID}
    assert sources.owners == ("finscope_2024", "eicv7_2023_24")
    assert shared["survey_estimates"].owned == {EICV7_SOURCE_ID}


def _estimate_part(partition: tuple[str, object]) -> TableRows:
    return TableRows(SurveyEstimate, None, estimate_rows()[:1], partition=partition)


def _source_part(source_id: str, partition: tuple[str, object] | None) -> TableRows:
    return TableRows(StatisticalSource, None, ({**SOURCE, "id": source_id},), partition=partition)


@pytest.mark.parametrize(
    ("parts", "message"),
    [
        ((_source_part("a", ("id", "a")), _source_part("a", ("id", "a"))), "both claim"),
        ((_source_part("a", ("id", "a")), _source_part("b", None)), "both partitioned and not"),
        (
            (_estimate_part(("source_id", EICV7_SOURCE_ID)), _estimate_part(("table_id", "A9.23"))),
            "partitioned by both",
        ),
    ],
)
def test_conflicting_partitions_are_refused(parts: tuple[TableRows, ...], message: str) -> None:
    def build(part: TableRows) -> Callable[[], tuple[TableRows, ...]]:
        return lambda: (part,)

    datasets = [Dataset(f"d{i}", build(part)) for i, part in enumerate(parts)]
    with pytest.raises(ValueError, match=message):
        shared_tables(datasets)


def test_partition_column_must_be_in_the_primary_key() -> None:
    """Otherwise ON CONFLICT (primary key) could overwrite a row in another partition."""
    bad = Dataset("bad", lambda: (_source_part("a", ("title", SOURCE["title"])),))
    with pytest.raises(ValueError, match="not in the primary key"):
        _ = bad.tables

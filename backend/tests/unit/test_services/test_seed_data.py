"""Seed datasets: design values, determinism, [SYN] construction rules and hash stability."""

import ast
from collections import Counter
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from app.calculations import is_in_deficit, vulnerability_score
from app.data import DATASETS
from app.data import synthetic_households as synthetic
from app.data.reference import BENCHMARK_AMOUNTS, DISTRICT_CODES
from app.data.registry import content_hash
from app.data.vulnerability import DESIGN_SCORES, WEIGHTS, component_table


def test_dataset_names_are_unique_and_ordered_parents_first() -> None:
    names = [d.name for d in DATASETS]
    assert len(names) == len(set(names))
    assert names.index("methodology") < names.index("districts") < names.index("budget_benchmarks")
    assert names.index("dashboard_dimensions") < names.index("vulnerability")


def test_thirty_districts_alphabetical_starting_with_bugesera() -> None:
    assert len(DISTRICT_CODES) == 30
    assert list(DISTRICT_CODES) == sorted(DISTRICT_CODES)
    assert DISTRICT_CODES[0] == "bugesera"


def test_benchmark_lines_total_the_design_essentials() -> None:
    assert sum(BENCHMARK_AMOUNTS.values()) == 150_000


def test_design_scores_and_top_six() -> None:
    top = sorted(DESIGN_SCORES.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    assert top == [
        ("nyagatare", 74),
        ("bugesera", 71),
        ("kirehe", 68),
        ("gatsibo", 66),
        ("gisagara", 64),
        ("nyaruguru", 63),
    ]
    assert DESIGN_SCORES["gasabo"] == 46


def test_components_reproduce_every_design_score() -> None:
    components = component_table()
    assert components["gasabo"] == (50, 40, 50)
    for code, triple in components.items():
        assert all(0 <= value <= 100 for value in triple)
        assert vulnerability_score(triple, WEIGHTS) == Decimal(DESIGN_SCORES[code])


def test_synthetic_sample_hits_the_design_totals_exactly() -> None:
    rows = synthetic.generate()
    assert len(rows) == 3_000
    assert Counter(r["primary_income_source"] for r in rows) == {
        "wage": 1_200,
        "agriculture": 1_050,
        "informal_enterprise": 750,
    }
    assert Counter(r["district_code"] for r in rows) == dict.fromkeys(DISTRICT_CODES, 100)
    deficits = sum(
        is_in_deficit(int(str(r["monthly_income"])), int(str(r["monthly_essentials"])), 20)
        for r in rows
    )
    assert deficits == 1_000


def test_synthetic_sample_is_deterministic() -> None:
    assert synthetic.generate() == synthetic.generate()


def test_generator_never_reads_vulnerability_data() -> None:
    """Deficit selection is independent of vulnerability scores (plan F6)."""
    source = Path(synthetic.__file__).read_text(encoding="utf-8")
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert not any("vulnerability" in name for name in imported)


def test_content_hashes_are_stable_and_change_with_content() -> None:
    rows: list[Mapping[str, object]] = [{"a": 1, "b": Decimal("1.00")}, {"a": 2, "b": None}]
    assert content_hash([("t", rows)]) == content_hash([("t", list(reversed(rows)))])
    one: list[Mapping[str, object]] = [{"a": 1, "b": Decimal("1")}]
    one_padded: list[Mapping[str, object]] = [{"a": 1, "b": Decimal("1.00")}]
    assert content_hash([("t", one)]) == content_hash([("t", one_padded)])
    assert content_hash([("t", rows)]) != content_hash([("t", rows[:1])])
    assert content_hash([("t", rows)]) != content_hash([("u", rows)])


def test_every_dataset_builds_and_has_a_hash() -> None:
    for dataset in DATASETS:
        assert len(dataset.content_hash) == 64
        assert all(part.rows for part in dataset.tables)

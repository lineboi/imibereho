"""FinScope Rwanda 2024 transcription: every published value, plus the report's own cross-checks.

Values were verified against "Finscope-Final-Report__10_07_2024-1.pdf" (SHA-256 981727b8…),
pages 25, 27, 69 and 31. If a value here changes, re-verify it against the report first.
"""

import re
from collections import Counter

import pytest

from app.data import DATASETS
from app.data.finscope_2024 import DISTRICT_NOTES, DISTRICTS, NATIONAL, SOURCE
from app.data.reference import DISTRICT_CODES

BY_CODE = {row[0]: row for row in NATIONAL}


def national(code: str) -> tuple[int, int | None]:
    row = BY_CODE[code]
    return row[4], row[6]  # 2024 value, 2020 comparison


@pytest.mark.parametrize(
    ("code", "value_2024", "value_2020", "page"),
    [
        ("financially_included", 96, 93, 25),
        ("formally_served", 92, 77, 25),
        ("financially_excluded", 4, 7, 25),
        ("financially_healthy", 10, 4, 69),
        ("financially_vulnerable", 31, 37, 69),
    ],
)
def test_requested_national_indicators_match_the_report(
    code: str, value_2024: int, value_2020: int, page: int
) -> None:
    assert national(code) == (value_2024, value_2020)
    assert BY_CODE[code][8] == page


def test_access_strand_values_and_sums() -> None:
    strand = [
        "banked",
        "other_formal_non_bank_only",
        "informal_only",
        "financially_excluded_strand",
    ]
    assert [national(c)[0] for c in strand] == [22, 70, 4, 4]  # Figure 5, 2024
    assert [national(c)[1] for c in strand] == [22, 55, 16, 7]  # Figure 5, 2020
    assert sum(national(c)[0] for c in strand) == 100
    assert sum(national(c)[1] or 0 for c in strand) == 100
    # Formally served = banked + other formal (non-bank) only, in both years (Figure 5 labels).
    assert national("banked")[0] + national("other_formal_non_bank_only")[0] == 92
    assert (national("banked")[1] or 0) + (national("other_formal_non_bank_only")[1] or 0) == 77


def test_financial_health_strand_as_printed_including_rounding() -> None:
    codes = [
        "financially_extremely_vulnerable",
        "financially_vulnerable",
        "financially_coping",
        "financially_healthy",
    ]
    assert [national(c)[0] for c in codes] == [3, 31, 57, 10]  # Figure 65, 2024
    assert [national(c)[1] for c in codes] == [7, 37, 53, 4]  # Figure 65, 2020
    # The report warns percentages may not add to 100 (p. 21); both rows print 101.
    assert sum(national(c)[0] for c in codes) == 101


def test_counts_are_omitted_where_the_report_contradicts_itself() -> None:
    for code, quoted in (
        ("financially_excluded", ("316,000", "317,000")),
        ("informal_only", ("358,000", "317,000")),
        ("financially_healthy", ("778k", "780,000")),
    ):
        row = BY_CODE[code]
        assert row[5] is None, code  # no 2024 count published
        assert all(q in (row[10] or "") for q in quoted), code


def test_every_national_indicator_cites_a_page_and_figure() -> None:
    for row in NATIONAL:
        page, figure = row[8], row[9]
        assert page in {25, 27, 69}
        assert re.search(r"Figure \d+", figure), row[0]


def test_comparisons_exist_only_where_published() -> None:
    assert all(row[6] is not None for row in NATIONAL)  # every printed figure has a 2020 bar
    figure_only = {
        "financially_coping",
        "financially_vulnerable",
        "financially_extremely_vulnerable",
    }
    for code in figure_only:
        assert "Figure 65 only" in (BY_CODE[code][10] or "")


def test_thirty_districts_matching_the_reference_list() -> None:
    assert set(DISTRICTS) == set(DISTRICT_CODES)
    assert len(DISTRICTS) == 30


def test_report_prose_twelve_districts_above_national_exclusion() -> None:
    """p. 30: 'Twelve districts have higher levels of financial exclusion than ... 4%'."""
    above = {code for code, row in DISTRICTS.items() if row[3] > 4}
    assert len(above) == 12
    top_five = sorted(DISTRICTS, key=lambda c: (-DISTRICTS[c][3], c))[:5]
    # p. 30: '... especially Nyaruguru, Ngoma, Rulindo, Nyabihu and Gakenke'.
    assert set(top_five) == {"nyaruguru", "ngoma", "rulindo", "nyabihu", "gakenke"}


def test_report_prose_gicumbi_highest_informal_only() -> None:
    informal = {code: row[2] for code, row in DISTRICTS.items() if row[2] is not None}
    assert max(informal, key=lambda c: informal[c]) == "gicumbi"
    assert Counter(informal.values())[informal["gicumbi"]] == 1


def test_report_prose_bank_led_districts() -> None:
    """p. 30: inclusion is bank led only in Kicukiro, Nyarugenge and Gasabo."""
    bank_led = {code for code, row in DISTRICTS.items() if row[0] > row[1]}
    assert bank_led == {"kicukiro", "nyarugenge", "gasabo"}


def test_district_rows_sum_within_rounding() -> None:
    for code, (banked, other, informal, excluded) in DISTRICTS.items():
        if informal is None:
            continue
        assert 99 <= banked + other + informal + excluded <= 101, code


def test_unlabelled_segment_is_null_not_zero_and_explained() -> None:
    assert DISTRICTS["nyarugenge"] == (59, 40, None, 1)
    assert set(DISTRICT_NOTES) == {"nyarugenge"}
    assert "not assumed to be 0" in DISTRICT_NOTES["nyarugenge"]


def test_source_provenance_is_complete() -> None:
    assert SOURCE["publisher"] == "Access to Finance Rwanda (AFR)"
    assert SOURCE["citation"] == "Access to Finance Rwanda, FinScope 2024 report, June 2024"
    assert SOURCE["fieldwork_period"] is None  # not stated in the report
    assert SOURCE["sample_size"] == 13_994
    assert re.fullmatch(r"[0-9a-f]{64}", str(SOURCE["document_sha256"]))
    assert str(SOURCE["document_url"]).startswith("https://microdata.statistics.gov.rw/")


def test_dataset_is_registered_after_districts() -> None:
    names = [d.name for d in DATASETS]
    assert names.index("districts") < names.index("finscope_2024")

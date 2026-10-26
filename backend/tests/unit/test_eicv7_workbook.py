"""The EICV7 workbook extractor and the stdlib .xlsx reader, on synthetic workbooks.

The real workbook is not in the repository. These tests rebuild its two sheets from the
transcription, in the same layout, and check that the extractor reproduces the transcription
exactly and rejects every layout surprise instead of skipping rows.
"""

import ast
import zipfile
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from app.data import eicv7_workbook as workbook
from app.data.eicv7_2023_24 import HEALTH_INSURANCE, POVERTY, TABLES, Row, TableSpec
from app.data.xlsx_reader import WorkbookError, read_cells, sheet_names

Cell = str | Decimal  # str -> shared string, Decimal -> number written verbatim
Sheet = dict[tuple[int, str], Cell]
NS: Final = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
REL_NS: Final = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
BY_TABLE: Final = {"A9.23": POVERTY, "A3.7": HEALTH_INSURANCE}


def write_workbook(path: Path, sheets: dict[str, Sheet], inline: Sheet | None = None) -> Path:
    shared: list[str] = []
    parts: dict[str, str] = {}
    entries, rels = [], []
    for index, (name, cells) in enumerate(sheets.items(), 1):
        rows: dict[int, list[str]] = {}
        for (row, col), value in sorted(cells.items()):
            if isinstance(value, Decimal):
                xml = f'<c r="{col}{row}"><v>{value}</v></c>'
            else:
                shared.append(value)
                xml = f'<c r="{col}{row}" t="s"><v>{len(shared) - 1}</v></c>'
            rows.setdefault(row, []).append(xml)
        for (row, col), value in (inline or {}).items() if index == 1 else ():
            rows.setdefault(row, []).append(
                f'<c r="{col}{row}" t="inlineStr"><is><t>{value}</t></is></c>'
            )
        body = "".join(f'<row r="{r}">{"".join(c)}</row>' for r, c in sorted(rows.items()))
        parts[f"xl/worksheets/sheet{index}.xml"] = (
            f"<worksheet {NS}><sheetData>{body}</sheetData></worksheet>"
        )
        entries.append(f'<sheet name="{name}" sheetId="{index}" r:id="rId{index}"/>')
        rels.append(f'<Relationship Id="rId{index}" Target="worksheets/sheet{index}.xml"/>')
    strings = "".join(f"<si><t>{s.replace('&', '&amp;')}</t></si>" for s in shared)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(
            "xl/workbook.xml",
            f'<workbook {NS} xmlns:r="{REL_NS}"><sheets>{"".join(entries)}</sheets></workbook>',
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{''.join(rels)}</Relationships>",
        )
        archive.writestr("xl/sharedStrings.xml", f"<sst {NS}>{strings}</sst>")
        for name, xml in parts.items():
            archive.writestr(name, xml)
    return path


def table_sheet(spec: TableSpec, rows: tuple[Row, ...], footnote: str | None = None) -> Sheet:
    """The sheet as NISR lays it out: title, header, national row, then labelled sections."""
    sheet: Sheet = {(1, "A"): spec.title, (2, "B"): spec.value_header}
    for col, header in zip("CDEFG", workbook.UNCERTAINTY_HEADERS, strict=True):
        sheet[(2, col)] = header
    section_of = {dimension: label for label, dimension in spec.sections.items()}
    number, current = 2, "national"
    for dimension, _, label, *values in rows:
        number += 1
        if dimension != current:
            sheet[(number, "A")] = section_of[dimension]
            current, number = dimension, number + 1
        sheet[(number, "A")] = label
        for col, value in zip("BCDEFG", values, strict=True):
            if value is not None:
                sheet[(number, col)] = Decimal(value)
    if footnote:
        sheet[(number + 1, "A")] = footnote
    return sheet


def real_layout() -> dict[str, Sheet]:
    poverty, health = TABLES
    return {
        "Table of Contents": {(1, "B"): "NATIONAL INSTITUTE OF STATISTICS OF RWANDA"},
        poverty.sheet: table_sheet(poverty, POVERTY),
        health.sheet: table_sheet(health, HEALTH_INSURANCE, "Source: NISR, EICV7"),
    }


@pytest.fixture
def xlsx(tmp_path: Path) -> Path:
    return write_workbook(tmp_path / "eicv7.xlsx", real_layout())


def with_cells(
    tmp_path: Path, table: int, changes: Sheet, drop: tuple[tuple[int, str], ...] = ()
) -> Path:
    sheets = real_layout()
    sheet = sheets[TABLES[table].sheet]
    for key in drop:
        del sheet[key]
    sheet.update(changes)
    return write_workbook(tmp_path / "changed.xlsx", sheets)


# --- The reader ---


def test_reader_returns_strings_and_verbatim_numbers(tmp_path: Path) -> None:
    path = write_workbook(
        tmp_path / "w.xlsx",
        {"S": {(1, "A"): "label & more", (1, "B"): Decimal("0.90542229193848334")}},
        inline={(2, "A"): "inline text"},
    )
    assert sheet_names(path) == ["S"]
    assert read_cells(path, "S") == {
        (1, "A"): "label & more",
        (1, "B"): "0.90542229193848334",  # not float-rounded to 0.9054222919384833
        (2, "A"): "inline text",
    }


def test_reader_errors(tmp_path: Path, xlsx: Path) -> None:
    with pytest.raises(WorkbookError, match="not found"):
        read_cells(xlsx, "Table A9.99")
    not_xlsx = tmp_path / "x.xlsx"
    not_xlsx.write_bytes(b"%PDF-1.7")
    with pytest.raises(WorkbookError, match="not a readable"):
        read_cells(not_xlsx, "S")
    empty = tmp_path / "empty.xlsx"
    with zipfile.ZipFile(empty, "w") as archive:
        archive.writestr("other.txt", "")
    with pytest.raises(WorkbookError, match="missing"):
        sheet_names(empty)


# --- Extraction reproduces the transcription ---


def test_extraction_matches_the_transcription_exactly(xlsx: Path) -> None:
    for spec in TABLES:
        extracted = workbook.extract(xlsx, spec)
        assert [r for _, r in extracted.rows] == list(BY_TABLE[spec.table_id])
        assert workbook.compare(extracted, BY_TABLE[spec.table_id]) == []
        assert extracted.blank_value_cells == ()
    assert workbook.extract(xlsx, TABLES[1]).footnotes == ("Source: NISR, EICV7",)


def test_literals_mode_regenerates_the_module_data(
    xlsx: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert workbook.main([str(xlsx), "--literals"]) == 0
    printed = capsys.readouterr().out
    for name, expected in (("POVERTY", POVERTY), ("HEALTH_INSURANCE", HEALTH_INSURANCE)):
        header = f"{name}: Final[tuple[Row, ...]] = "
        start = printed.index(header) + len(header)
        body = printed[start : printed.index(")  # fmt: skip", start) + 1]
        assert ast.literal_eval(body) == expected


def test_verify_reports_counts_and_success(xlsx: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert workbook.main([str(xlsx)]) == 0
    out = capsys.readouterr().out
    assert "Table A9.23 (Table A9.23): 38 records, 228 values" in out
    assert "national 1, sex 2, area 2, province 5, quintile 5, district 30" in out
    assert "DIFFERS FROM the registered source" in out  # a rebuilt file, not NISR's bytes
    assert "result: every value matches the transcription" in out


# --- Differences are reported, never hidden ---


def test_a_changed_value_fails_verification(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = with_cells(tmp_path, 0, {(3, "B"): Decimal("27.36")})
    assert workbook.main([str(path)]) == 1
    assert "MISMATCH A9.23 row 3" in capsys.readouterr().out


def test_a_blank_cell_is_none_and_reported(tmp_path: Path) -> None:
    path = with_cells(tmp_path, 0, {}, drop=((3, "C"),))
    extracted = workbook.extract(path, TABLES[0])
    assert extracted.blank_value_cells == ("C3",)
    assert extracted.rows[0][1][4] is None
    assert workbook.compare(extracted, POVERTY)  # differs from the transcription


def test_a_missing_row_is_reported(xlsx: Path) -> None:
    extracted = workbook.extract(xlsx, TABLES[0])
    problems = workbook.compare(extracted, (*POVERTY, POVERTY[0]))
    assert problems == ["A9.23: 38 rows vs 39"]


@pytest.mark.parametrize(
    ("changes", "drop", "message"),
    [
        ({(1, "A"): "Table A9.23: something else"}, (), "title is"),
        ({(2, "C"): "SE"}, (), "unexpected header"),
        ({(4, "H"): Decimal(1)}, (), "outside columns A-G"),
        ({(4, "A"): "Areas"}, (), "unknown label"),
        ({(5, "A"): "Suburban"}, (), "unknown area"),
        ({(14, "A"): "Kigali"}, (), "unknown district"),
        ({(5, "B"): "n/a"}, (), "is not a number"),
        ({(5, "B"): Decimal("NaN")}, (), "not a finite number"),
        ({}, ((5, "A"),), "values without a row label"),
        ({(3, "A"): "Rwanda"}, (), "national row labelled"),
        ({(4, "A"): "Poverty Rate", (4, "B"): Decimal(1)}, (), "second row before any section"),
    ],
)
def test_layout_surprises_stop_the_extractor(
    tmp_path: Path, changes: Sheet, drop: tuple[tuple[int, str], ...], message: str
) -> None:
    path = with_cells(tmp_path, 0, changes, drop)
    with pytest.raises(workbook.LayoutError, match=message):
        workbook.extract(path, TABLES[0])


def test_a_row_without_an_estimate_stops_the_extractor(tmp_path: Path) -> None:
    path = with_cells(tmp_path, 0, {}, drop=((5, "B"),))
    with pytest.raises(workbook.LayoutError, match="no estimate"):
        workbook.extract(path, TABLES[0])


def test_unreadable_input_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert workbook.main([str(tmp_path / "missing.xlsx")]) == 2
    assert "cannot read the workbook" in capsys.readouterr().err

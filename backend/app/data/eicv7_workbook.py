"""Extract and verify EICV7 annex tables A9.23 and A3.7 from NISR's published workbook.

    uv run python -m app.data.eicv7_workbook <path to EICV7_Tables_MainIndicatorReport.xlsx>
    uv run python -m app.data.eicv7_workbook <path> --literals   # print the rows as Python

The first form re-reads both tables cell by cell and compares every value with the transcription
in `app/data/eicv7_2023_24.py` (exact text, so exact `Decimal` equality). It reports the file's
SHA-256, record counts by dimension, blank cells and footnotes. It exits 0 only when every value
matches, 1 on any difference and 2 when the workbook cannot be read or its layout is unexpected.

The parser is strict on purpose: an unknown row label, a non-numeric value, a cell outside
columns A-G or a changed header stops it, rather than a row being skipped silently.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final

from app.data.eicv7_2023_24 import (
    HEALTH_INSURANCE,
    POVERTY,
    SOURCE,
    TABLES,
    Row,
    TableSpec,
    category_code,
)
from app.data.xlsx_reader import WorkbookError, read_cells

VALUE_COLUMNS: Final = ("B", "C", "D", "E", "F", "G")
UNCERTAINTY_HEADERS: Final = (
    "Std. error (%)",
    "95%CI lower bound",
    "95%CI upper bound",
    "CV (%)",
    "Design effect",
)
TRANSCRIBED: Final = {"A9.23": POVERTY, "A3.7": HEALTH_INSURANCE}


class LayoutError(ValueError):
    """The sheet does not have the layout this extractor was written for."""


@dataclass(frozen=True, slots=True)
class Extracted:
    spec: TableSpec
    rows: tuple[tuple[int, Row], ...]  # (sheet row number, transcription row)
    footnotes: tuple[str, ...]
    blank_value_cells: tuple[str, ...]


def _numeric(text: str, where: str) -> str:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LayoutError(f"{where}: {text!r} is not a number") from exc
    if not value.is_finite():
        raise LayoutError(f"{where}: {text!r} is not a finite number")
    return text


def extract(path: Path, spec: TableSpec) -> Extracted:
    cells = read_cells(path, spec.sheet)
    stray = sorted(f"{col}{row}" for row, col in cells if col not in ("A", *VALUE_COLUMNS))
    if stray:
        raise LayoutError(f"{spec.sheet}: cells outside columns A-G: {stray}")
    if cells.get((1, "A")) != spec.title:
        raise LayoutError(f"{spec.sheet}: title is {cells.get((1, 'A'))!r}")
    header = tuple(cells.get((2, col)) for col in VALUE_COLUMNS)
    if header != (spec.value_header, *UNCERTAINTY_HEADERS):
        raise LayoutError(f"{spec.sheet}: unexpected header {header}")

    rows: list[tuple[int, Row]] = []
    footnotes: list[str] = []
    blanks: list[str] = []
    dimension = "national"
    last_row = max(row for row, _ in cells)
    for number in range(3, last_row + 1):
        label = cells.get((number, "A"))
        raw = [cells.get((number, col)) for col in VALUE_COLUMNS]
        if label is None:
            if any(raw):
                raise LayoutError(f"{spec.sheet} row {number}: values without a row label")
            continue
        if not any(raw):
            if label.startswith("Source:"):
                footnotes.append(label)
            elif label in spec.sections:
                dimension = spec.sections[label]
            else:
                raise LayoutError(f"{spec.sheet} row {number}: unknown label {label!r}")
            continue
        if dimension == "national" and rows:
            raise LayoutError(f"{spec.sheet} row {number}: a second row before any section")
        if dimension == "national" and label != spec.national_label:
            raise LayoutError(f"{spec.sheet} row {number}: national row labelled {label!r}")
        blanks.extend(
            f"{col}{number}" for col, text in zip(VALUE_COLUMNS, raw, strict=True) if text is None
        )
        estimate, se, lower, upper, cv, deff = (
            _numeric(text, f"{spec.sheet}!{col}{number}") if text is not None else None
            for col, text in zip(VALUE_COLUMNS, raw, strict=True)
        )
        if estimate is None:
            raise LayoutError(f"{spec.sheet} row {number}: no estimate for {label!r}")
        try:
            code = category_code(dimension, label)
        except KeyError as exc:
            raise LayoutError(f"{spec.sheet} row {number}: {exc.args[0]}") from exc
        rows.append((number, (dimension, code, label, estimate, se, lower, upper, cv, deff)))
    return Extracted(spec, tuple(rows), tuple(footnotes), tuple(blanks))


def compare(extracted: Extracted, transcribed: Sequence[Row]) -> list[str]:
    """Every difference between the workbook and the transcription, as readable lines."""
    problems: list[str] = []
    found = [row for _, row in extracted.rows]
    if len(found) != len(transcribed):
        problems.append(f"{extracted.spec.table_id}: {len(found)} rows vs {len(transcribed)}")
    for (number, row), expected in zip(extracted.rows, transcribed, strict=False):
        if row != expected:
            problems.append(f"{extracted.spec.table_id} row {number}: {row} != {expected}")
    return problems


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def _literal(value: str | None) -> str:
    return "None" if value is None else json.dumps(value, ensure_ascii=False)


def literals(extracted: Extracted, name: str) -> str:
    """The rows as the Python assignment used in app/data/eicv7_2023_24.py."""
    lines = [
        f"# Table {extracted.spec.table_id} ({extracted.spec.sheet}), rows {extracted.rows[0][0]}"
        f"-{extracted.rows[-1][0]}, extracted by app.data.eicv7_workbook --literals.",
        f"{name}: Final[tuple[Row, ...]] = (",
    ]
    for _, row in extracted.rows:
        head = ", ".join(_literal(value) for value in row[:3])
        lines.append(f"    ({head},")
        lines.append(f"     {', '.join(_literal(value) for value in row[3:6])},")
        lines.append(f"     {', '.join(_literal(value) for value in row[6:])}),")
    lines.append(")  # fmt: skip")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.data.eicv7_workbook", description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--literals", action="store_true", help="print rows as Python tuples")
    parsed = parser.parse_args(argv)
    path: Path = parsed.workbook
    try:
        digest = sha256(path)
        extracted = [extract(path, spec) for spec in TABLES]
    except (OSError, WorkbookError, LayoutError) as exc:
        print(f"cannot read the workbook: {exc}", file=sys.stderr)
        return 2
    if parsed.literals:
        names = {"A9.23": "POVERTY", "A3.7": "HEALTH_INSURANCE"}
        print("\n\n".join(literals(table, names[table.spec.table_id]) for table in extracted))
        return 0

    expected_digest = SOURCE["document_sha256"]
    print(f"file: {path.name} ({path.stat().st_size} bytes)")
    print(f"sha256: {digest} ({'matches' if digest == expected_digest else 'DIFFERS FROM'} the "
          f"registered source)")  # fmt: skip
    problems: list[str] = []
    for table in extracted:
        counts = Counter(row[0] for _, row in table.rows)
        values = sum(1 for _, row in table.rows for value in row[3:] if value is not None)
        print(
            f"Table {table.spec.table_id} ({table.spec.sheet}): {len(table.rows)} records, "
            f"{values} values; " + ", ".join(f"{dim} {n}" for dim, n in counts.items())
        )
        print(f"  blank value cells: {list(table.blank_value_cells) or 'none'}")
        print(f"  footnotes: {list(table.footnotes) or 'none'}")
        problems.extend(compare(table, TRANSCRIBED[table.spec.table_id]))
    for problem in problems:
        print(f"MISMATCH {problem}")
    print("result: every value matches the transcription" if not problems else "result: FAILED")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Read the raw cell text of one worksheet in an .xlsx workbook, with the standard library only.

Numbers come back exactly as the workbook stores them (the `<v>` text, e.g. "27.362976067289672"),
never via `float`, so a published value can be compared with, or turned into, a `Decimal` with
no rounding. The workbook is opened read-only and never written.
"""

import posixpath
import zipfile
from pathlib import Path
from typing import Final
from xml.etree import ElementTree as ET  # input: an official workbook named by the operator

_MAIN: Final = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL: Final = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_PKG_REL: Final = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# (row number, column letters) -> raw text. Empty cells are absent.
Cells = dict[tuple[int, str], str]


class WorkbookError(ValueError):
    """The file is not a readable workbook, or the sheet is missing."""


def _parse(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        return ET.fromstring(archive.read(name))  # noqa: S314 (see the import note)
    except KeyError as exc:
        raise WorkbookError(f"workbook part {name} is missing") from exc


def _text(element: ET.Element) -> str:
    """Concatenated text of every <t> below `element` (rich text has several runs)."""
    return "".join(node.text or "" for node in element.iter(f"{_MAIN}t"))


def _shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = _parse(archive, "xl/sharedStrings.xml")
    return [_text(item) for item in root.findall(f"{_MAIN}si")]


def _sheet_part(archive: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = _parse(archive, "xl/workbook.xml")
    relationships = _parse(archive, "xl/_rels/workbook.xml.rels")
    targets = {rel.get("Id"): rel.get("Target", "") for rel in relationships}
    for sheet in workbook.iter(f"{_MAIN}sheet"):
        if sheet.get("name") == sheet_name:
            target = targets.get(sheet.get(f"{_REL}id"), "")
            if target.startswith("/"):
                return target.lstrip("/")
            return posixpath.normpath(posixpath.join("xl", target))
    raise WorkbookError(f"sheet {sheet_name!r} not found")


def _split_reference(reference: str) -> tuple[int, str]:
    letters = "".join(ch for ch in reference if ch.isalpha())
    return int(reference[len(letters) :]), letters


def sheet_names(path: Path) -> list[str]:
    with _open(path) as archive:
        workbook = _parse(archive, "xl/workbook.xml")
        return [str(sheet.get("name")) for sheet in workbook.iter(f"{_MAIN}sheet")]


def read_cells(path: Path, sheet_name: str) -> Cells:
    """Every non-empty cell of `sheet_name` as raw text (strings resolved, numbers verbatim)."""
    with _open(path) as archive:
        shared = _shared_strings(archive)
        root = _parse(archive, _sheet_part(archive, sheet_name))
        cells: Cells = {}
        for cell in root.iter(f"{_MAIN}c"):
            kind = cell.get("t", "n")
            if kind == "inlineStr":
                inline = cell.find(f"{_MAIN}is")
                value = _text(inline) if inline is not None else ""
            else:
                raw = cell.find(f"{_MAIN}v")
                if raw is None or raw.text is None:
                    continue
                value = shared[int(raw.text)] if kind == "s" else raw.text
            if value.strip():
                cells[_split_reference(str(cell.get("r")))] = value
        return cells


def _open(path: Path) -> zipfile.ZipFile:
    try:
        return zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as exc:
        raise WorkbookError(f"{path.name} is not a readable .xlsx workbook: {exc}") from exc

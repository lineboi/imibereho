"""Seed dataset definitions and canonical content hashing (plan A3 seed framework).

A dataset is a named function returning rows for one or more tables, parents first. A table is
either *global* (`scope_column` None: rows are upserted and rows absent from the set are
deleted) or *version-scoped* (rows for the current methodology version are replaced).
"""

import hashlib
import json
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from functools import cached_property
from typing import cast

from sqlalchemy import Table

from app.db.base import Base


@dataclass(frozen=True, slots=True)
class TableRows:
    model: type[Base]
    scope_column: str | None
    rows: tuple[Mapping[str, object], ...]
    # For a global table that several datasets share (e.g. one row per official source in
    # `statistical_sources`): (column, value) limits this dataset's sync, stale-row delete and
    # hash check to its own rows. It does not enter the content hash.
    partition: tuple[str, object] | None = None

    @property
    def table(self) -> Table:
        return cast(Table, self.model.__table__)

    @property
    def columns(self) -> tuple[str, ...]:
        return tuple(self.table.columns.keys()) if not self.rows else tuple(self.rows[0].keys())


@dataclass(frozen=True)
class Dataset:
    name: str
    build: Callable[[], tuple[TableRows, ...]]

    @cached_property
    def tables(self) -> tuple[TableRows, ...]:
        tables = self.build()
        for part in tables:
            keys = {frozenset(row.keys()) for row in part.rows}
            if len(keys) > 1:
                raise ValueError(f"{self.name}: rows for {part.table.name} have differing columns")
            if part.partition is not None:
                column, value = part.partition
                # In the key, so an upsert can never take over another partition's row.
                if column not in part.table.primary_key.columns:
                    raise ValueError(
                        f"{self.name}: partition column {part.table.name}.{column} is not in "
                        "the primary key"
                    )
                if any(row[column] != value for row in part.rows):
                    raise ValueError(
                        f"{self.name}: a row for {part.table.name} is outside its partition"
                    )
        return tables

    @cached_property
    def content_hash(self) -> str:
        return content_hash((part.table.name, part.rows) for part in self.tables)


@dataclass(frozen=True, slots=True)
class SharedTable:
    """A table split between datasets by `column`; `owned` holds every claimed value."""

    table: Table
    column: str
    owned: frozenset[object]
    owners: tuple[str, ...]  # dataset names, in registry order


def shared_tables(datasets: Iterable[Dataset]) -> dict[str, SharedTable]:
    """Every partitioned table, in first-use order (parents first).

    Raises ValueError if a table mixes partitioned and unpartitioned datasets, uses two
    partition columns, or if two datasets claim the same partition value.
    """
    found: dict[str, tuple[Table, str, dict[object, str]]] = {}
    unpartitioned: set[str] = set()
    for dataset in datasets:
        for part in dataset.tables:
            name = part.table.name
            if part.partition is None:
                unpartitioned.add(name)
                continue
            column, value = part.partition
            _, known_column, owners = found.setdefault(name, (part.table, column, {}))
            if known_column != column:
                raise ValueError(f"{name}: partitioned by both {known_column} and {column}")
            owner = owners.setdefault(value, dataset.name)
            if owner != dataset.name:
                raise ValueError(f"{name}: {dataset.name} and {owner} both claim {value!r}")
    mixed = sorted(unpartitioned & found.keys())
    if mixed:
        raise ValueError(f"tables both partitioned and not: {mixed}")
    return {
        name: SharedTable(table, column, frozenset(owners), tuple(dict.fromkeys(owners.values())))
        for name, (table, column, owners) in found.items()
    }


def _canonical_value(value: object) -> object:
    if isinstance(value, Decimal):
        # 1.00 and 1 hash the same: the database returns NUMERIC(6,2) values with trailing zeros.
        normalised = value.normalize()
        return {"decimal": format(normalised, "f")}
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, date) and not isinstance(value, datetime):
        return {"date": value.isoformat()}
    raise TypeError(f"unsupported seed value type {type(value).__name__}")


def canonical_rows(rows: Iterable[Mapping[str, object]]) -> list[str]:
    return sorted(
        json.dumps(
            {key: _canonical_value(value) for key, value in row.items()},
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        for row in rows
    )


def content_hash(tables: Iterable[tuple[str, Iterable[Mapping[str, object]]]]) -> str:
    """SHA-256 over each table's sorted, canonicalised rows, in table order."""
    digest = hashlib.sha256()
    for name, rows in tables:
        digest.update(name.encode())
        for line in canonical_rows(rows):
            digest.update(b"\n")
            digest.update(line.encode())
        digest.update(b"\x00")
    return digest.hexdigest()

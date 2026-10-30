"""Export every seed dataset to CSV in the repository's `data/` folder, one folder per dataset.

    uv run python scripts/export_data.py

Reads only the datasets registered in `app/data`, so it needs no database and no settings. The
CSV files are a readable copy; `app/data` stays the source that the seed and `/ready` check use.
"""

import csv
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from app.data import DATASETS

OUTPUT_DIR: Final = Path(__file__).resolve().parents[2] / "data"


def _cell(value: object) -> object:
    if isinstance(value, Mapping | list | tuple):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return value


def main() -> int:
    for dataset in DATASETS:
        for part in dataset.tables:
            if not part.rows:
                continue
            path = OUTPUT_DIR / dataset.name / f"{part.table.name}.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=part.columns, lineterminator="\n")
                writer.writeheader()
                writer.writerows(
                    {column: _cell(row[column]) for column in part.columns} for row in part.rows
                )
            print(f"[export] {path.relative_to(OUTPUT_DIR.parent)}: {len(part.rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

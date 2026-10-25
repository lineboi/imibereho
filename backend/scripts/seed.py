"""Guarded, idempotent seed entry point. Same as `python -m app.db.seed`.

    uv run python scripts/seed.py --target <dev|test|production> [--check]

Loads only the approved synthetic reference data registered in `app/data`. A rerun with nothing
changed commits nothing; `--check` verifies the table contents against the code.
"""

from app.db.seed import main

if __name__ == "__main__":
    raise SystemExit(main())

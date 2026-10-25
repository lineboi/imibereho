"""Guarded migration entry point. Same as `python -m app.db.migrate`.

    uv run python scripts/migrate.py --target <migrations|test|dev|production> <command> [args]

Examples:
    uv run python scripts/migrate.py --target dev upgrade head
    uv run python scripts/migrate.py --target migrations downgrade -1
"""

from app.db.migrate import main

if __name__ == "__main__":
    raise SystemExit(main())

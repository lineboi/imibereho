"""Alembic environment. Runs only when invoked through `app.db.migrate` (plan §2.3).

It never reads DATABASE_URL or any other variable itself: the wrapper resolves and guards the URL
for an explicit target and passes it in `config.attributes`. Without those attributes this file
refuses to run.
"""

from alembic import context

import app.models  # noqa: F401  # registers every table on Base.metadata
from app.db.base import Base
from app.db.migrate import (
    ATTR_ALLOW_LOCAL_SUPERUSER,
    ATTR_COMMAND,
    ATTR_ENVIRONMENT,
    ATTR_TARGET,
    ATTR_URL,
)
from app.db.session import create_guarded_engine

config = context.config
attributes = config.attributes

if not all(key in attributes for key in (ATTR_URL, ATTR_TARGET, ATTR_ENVIRONMENT, ATTR_COMMAND)):
    raise SystemExit(
        "Refusing to run Alembic directly. Use:\n"
        "    uv run python -m app.db.migrate --target <migrations|test|dev|production> <command>"
    )

if context.is_offline_mode():
    raise SystemExit("Offline (--sql) migrations are not supported.")

engine = create_guarded_engine(
    attributes[ATTR_URL],
    attributes[ATTR_TARGET],
    attributes[ATTR_ENVIRONMENT],
    attributes[ATTR_COMMAND],
    allow_local_superuser=bool(attributes.get(ATTR_ALLOW_LOCAL_SUPERUSER, False)),
)
try:
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
finally:
    engine.dispose()

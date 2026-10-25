"""The only Alembic entry point (plan §2.3, §2.10).

    uv run python -m app.db.migrate --target <migrations|test|dev|production> <command> [args]

The wrapper resolves the URL for the target from that target's variable only, guards it with the
command, prints `target, host/dbname` (never credentials), then calls Alembic's Python API with
the URL and target in `config.attributes`.
"""

import argparse
import sys
from collections.abc import Sequence
from typing import Final, get_args

from alembic import command as alembic_command
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.core.config import (
    BACKEND_DIR,
    InvalidSettingsError,
    MissingSettingError,
    Settings,
    Target,
    get_settings,
)
from app.db.guards import UnsafeDatabaseTargetError, assert_safe_target, describe_url

ATTR_URL: Final = "imibereho_url"
ATTR_TARGET: Final = "imibereho_target"
ATTR_ENVIRONMENT: Final = "imibereho_environment"
ATTR_COMMAND: Final = "imibereho_command"
ATTR_ALLOW_LOCAL_SUPERUSER: Final = "imibereho_allow_local_superuser"
ALEMBIC_INI: Final = BACKEND_DIR / "alembic.ini"

EXIT_REFUSED: Final = 2


def alembic_config() -> Config:
    return Config(str(ALEMBIC_INI))


def head_revision() -> str:
    """The single head revision of this build."""
    heads = ScriptDirectory.from_config(alembic_config()).get_heads()
    if len(heads) != 1:
        raise RuntimeError(f"expected exactly one Alembic head, found {len(heads)}")
    return heads[0]


def run(settings: Settings, target: Target, command: str, *args: str) -> None:
    """Guard, then run one Alembic command. Raises on refusal or missing configuration."""
    url = settings.database_url_for(target)
    assert_safe_target(
        url,
        target,
        settings.environment,
        command,
        allow_local_superuser=settings.allow_local_superuser,
    )
    print(
        f"[migrate] target={target} database={describe_url(url)} command={command} {' '.join(args)}"
    )
    config = alembic_config()
    config.attributes.update(
        {
            ATTR_URL: url,
            ATTR_TARGET: target,
            ATTR_ENVIRONMENT: settings.environment,
            ATTR_COMMAND: command,
            ATTR_ALLOW_LOCAL_SUPERUSER: settings.allow_local_superuser,
        }
    )
    match command:
        case "upgrade":
            alembic_command.upgrade(config, args[0] if args else "head")
        case "downgrade":
            if not args:
                raise ValueError("downgrade needs a revision, e.g. -1 or base")
            alembic_command.downgrade(config, args[0])
        case "check":
            alembic_command.check(config)
        case "current":
            alembic_command.current(config, verbose=False)
        case "heads":
            alembic_command.heads(config)
        case "history":
            alembic_command.history(config)
        case "stamp":
            if not args:
                raise ValueError("stamp needs a revision")
            alembic_command.stamp(config, args[0])
        case _:  # pragma: no cover - the guard has already refused unknown commands
            raise ValueError(f"unknown command {command!r}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.db.migrate", description=__doc__)
    parser.add_argument("--target", required=True, choices=get_args(Target))
    parser.add_argument("command")
    parser.add_argument("args", nargs="*")
    parsed = parser.parse_args(argv)
    try:
        run(get_settings(), parsed.target, parsed.command, *parsed.args)
    except (InvalidSettingsError, MissingSettingError, UnsafeDatabaseTargetError) as exc:
        print(f"[migrate] refused: {exc}", file=sys.stderr)
        return EXIT_REFUSED
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

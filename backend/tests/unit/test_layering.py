"""Layering rules (plan §2 item 4), enforced by scanning imports.

- `api` imports nothing from `repositories`, `models` or `db.session`.
- `repositories` import nothing from `services` or `api`.
- `calculations` imports nothing from the database, framework or other app layers.
- `services` never import `api`.
- Only the superuser integration test mentions the SUPERUSER_* variables.
"""

import ast
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
APP = BACKEND / "app"


def imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def modules(package: str) -> list[Path]:
    root = APP / package
    return sorted(root.rglob("*.py")) if root.is_dir() else [APP / f"{package}.py"]


@pytest.mark.parametrize(
    ("package", "forbidden"),
    [
        ("api", ("app.repositories", "app.models", "app.db.session", "sqlalchemy")),
        ("repositories", ("app.services", "app.api", "fastapi")),
        ("calculations", ("app.db", "app.repositories", "app.services", "app.api", "app.models",
                          "fastapi", "sqlalchemy")),
        ("services", ("app.api",)),
        ("schemas", ("app.db", "app.repositories", "app.services", "sqlalchemy")),
    ],
)  # fmt: skip
def test_layer_imports(package: str, forbidden: tuple[str, ...]) -> None:
    violations = [
        f"{path.relative_to(BACKEND)} imports {name}"
        for path in modules(package)
        for name in imports_of(path)
        if any(name == f or name.startswith(f + ".") for f in forbidden)
    ]
    assert not violations, violations


def test_api_v1_router_adds_no_prefix_and_the_central_router_mounts_it_once() -> None:
    v1_source = (APP / "api" / "v1" / "router.py").read_text(encoding="utf-8")
    central = (APP / "api" / "router.py").read_text(encoding="utf-8")
    assert "prefix" not in v1_source.split('"""', 2)[2]
    assert central.count("include_router(v1_router") == 1


def test_only_the_superuser_integration_test_reads_superuser_variables() -> None:
    allowed = BACKEND / "tests" / "security" / "test_superuser_refused.py"
    this_file = Path(__file__).resolve()
    offenders = []
    for path in [
        *APP.rglob("*.py"),
        *(BACKEND / "tests").rglob("*.py"),
        *(BACKEND / "scripts").rglob("*.py"),
    ]:
        if path.resolve() in {allowed, this_file}:
            continue
        text = path.read_text(encoding="utf-8")
        if "SUPERUSER_POSTGRES_DATABASE_URL" in text or "SUPERUSER_ALT_DATABASE_URL" in text:
            offenders.append(str(path.relative_to(BACKEND)))
    assert not offenders, offenders


def test_no_create_all_substitute_for_migrations() -> None:
    offenders = [
        str(path.relative_to(BACKEND))
        for path in [*APP.rglob("*.py"), *(BACKEND / "scripts").rglob("*.py")]
        if "create_all(" in path.read_text(encoding="utf-8")
    ]
    assert not offenders, offenders

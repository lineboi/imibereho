"""Live startup: a real uvicorn process, real HTTP, OpenAPI and /docs, and startup refusals."""

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx2 as httpx
import pytest

BACKEND = Path(__file__).resolve().parents[2]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
        return port


def clean_env(**values: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.endswith("DATABASE_URL")}
    # Blank values override anything in backend/.env, which the settings also read.
    env.update(
        {
            "DATABASE_URL": "",
            "ENVIRONMENT": "",
            "ALLOW_LOCAL_SUPERUSER": "false",
            "PYTHONUNBUFFERED": "1",
        }
    )
    env.update(values)
    return env


def start(app: str, env: dict[str, str], *extra: str) -> tuple[subprocess.Popen[str], int]:
    port = free_port()
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", app, *extra, "--port", str(port), "--no-access-log"],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, port


def wait_ready(process: subprocess.Popen[str], port: int, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            pytest.fail(f"server exited early ({process.returncode}):\n{output}")
        try:
            if httpx.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.2)
    pytest.fail("server did not start in time")


def stop(process: subprocess.Popen[str]) -> str:
    process.terminate()
    try:
        output, _ = process.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    return output or ""


@pytest.fixture
def stub_server() -> Iterator[tuple[str, subprocess.Popen[str]]]:
    process, port = start("tests.runtime.stub_server:build_stub", clean_env(), "--factory")
    try:
        wait_ready(process, port)
        yield f"http://127.0.0.1:{port}", process
    finally:
        stop(process)


def test_live_server_serves_health_docs_openapi_and_a_calculation(
    stub_server: tuple[str, subprocess.Popen[str]],
) -> None:
    base, process = stub_server
    assert httpx.get(f"{base}/health").json() == {"status": "ok"}
    docs = httpx.get(f"{base}/docs")
    assert docs.status_code == 200 and "swagger-ui" in docs.text
    schema = httpx.get(f"{base}/openapi.json").json()
    assert schema["info"]["version"] == "0.2.0"
    assert "/api/v1/calculations/household-shock" in schema["paths"]
    response = httpx.post(
        f"{base}/api/v1/calculations/household-shock?secretquery=1",
        json={
            "baseline": {"monthlyIncome": 424242, "monthlyEssentials": 1, "savings": 1},
            "shock": {"type": "income_fall", "incomeReductionPct": 20, "durationMonths": 3},
        },
    )
    assert response.status_code == 400 and response.headers["x-request-id"]
    output = stop(process)
    lines = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    assert any(line.get("path") == "/api/v1/calculations/household-shock" for line in lines)
    assert "424242" not in output and "secretquery" not in output


def test_server_refuses_to_start_in_ci_environment() -> None:
    process, _ = start("app.main:app", clean_env(ENVIRONMENT="ci"))
    output = process.communicate(timeout=60)[0]
    assert process.returncode != 0
    assert "does not run with ENVIRONMENT='ci'" in output


def test_server_refuses_to_start_without_database_url() -> None:
    process, _ = start("app.main:app", clean_env(ENVIRONMENT="local"))
    output = process.communicate(timeout=60)[0]
    assert process.returncode != 0
    assert "DATABASE_URL is not set" in output


def test_server_refuses_a_superuser_database_url_before_connecting() -> None:
    url = "postgresql://postgres:not-a-password@localhost:5432/imibereho"
    process, _ = start("app.main:app", clean_env(ENVIRONMENT="local", DATABASE_URL=url))
    output = process.communicate(timeout=60)[0]
    assert process.returncode != 0
    assert "superuser_name" in output and "not-a-password" not in output


def test_regression_production_refuses_to_start_with_the_local_superuser_opt_in() -> None:
    url = "postgresql://postgres:not-a-password@db.render.example:5432/imibereho"
    env = clean_env(ENVIRONMENT="production", DATABASE_URL=url, ALLOW_LOCAL_SUPERUSER="true")
    process, _ = start("app.main:app", env)
    output = process.communicate(timeout=60)[0]
    assert process.returncode != 0
    assert "ALLOW_LOCAL_SUPERUSER: has an invalid value" in output
    assert "not-a-password" not in output


def test_regression_production_refuses_postgres_without_the_opt_in() -> None:
    url = "postgresql://postgres:not-a-password@db.render.example:5432/imibereho"
    process, _ = start("app.main:app", clean_env(ENVIRONMENT="production", DATABASE_URL=url))
    output = process.communicate(timeout=60)[0]
    assert process.returncode != 0
    assert "superuser_name" in output and "not-a-password" not in output


def test_live_startup_against_the_test_database(db_settings: object) -> None:
    """Full startup: guard, superuser check on the first connection, version logged once."""
    env = dict(os.environ)
    process, port = start("tests.runtime.stub_server:build_test_db", env, "--factory")
    try:
        wait_ready(process, port)
        ready = httpx.get(f"http://127.0.0.1:{port}/ready")
        assert ready.status_code == 200, ready.text
    finally:
        output = stop(process)
    lines = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
    verified = [line for line in lines if line.get("message") == "database verified"]
    assert len(verified) == 1 and verified[0]["server_version_num"] >= 160000
    assert verified[0]["database"].endswith("/imibereho_test")

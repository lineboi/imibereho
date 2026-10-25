"""`/health` and `/ready` (contract §2)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.readiness import Readiness
from tests.helpers import assert_problem


def test_health_is_ok_without_touching_the_database(client: TestClient) -> None:
    response = client.get("/health")  # the stub app's database does not exist
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "meta" not in response.json()


def test_health_lives_at_the_root_only(client: TestClient) -> None:
    assert client.get("/api/v1/health").status_code == 404
    assert client.get("/api/v1/ready").status_code == 404


def test_ready_200_when_every_check_passes(stub_app: FastAPI) -> None:
    stub_app.state.readiness = lambda: Readiness("ok", "ok", "ok")
    response = TestClient(stub_app).get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"database": "ok", "migrations": "ok", "seed": "ok"},
    }


def test_ready_503_when_the_database_fails(stub_app: FastAPI) -> None:
    stub_app.state.readiness = lambda: Readiness("failed", "failed", "failed")
    body = assert_problem(TestClient(stub_app).get("/ready"), 503, "not-ready")
    assert body["checks"] == {"database": "failed", "migrations": "failed", "seed": "failed"}
    assert "meta" not in body


def test_ready_503_when_only_the_seed_is_stale(stub_app: FastAPI) -> None:
    stub_app.state.readiness = lambda: Readiness("ok", "ok", "failed")
    body = assert_problem(TestClient(stub_app).get("/ready"), 503, "not-ready")
    assert body["checks"] == {"database": "ok", "migrations": "ok", "seed": "failed"}


def test_ready_with_an_unreachable_database_reports_failed_checks(client: TestClient) -> None:
    """The real readiness function against a database that refuses the connection."""
    body = assert_problem(client.get("/ready"), 503, "not-ready")
    assert body["checks"] == {"database": "failed", "migrations": "failed", "seed": "failed"}


def test_ready_against_the_seeded_test_database(db_client: TestClient) -> None:
    response = db_client.get("/ready")
    assert response.status_code == 200, response.text
    assert response.json()["checks"] == {"database": "ok", "migrations": "ok", "seed": "ok"}

"""API versioning (mandatory), contract paths, OpenAPI metadata and CORS."""

from typing import Final

from fastapi import FastAPI
from fastapi.routing import iter_route_contexts
from fastapi.testclient import TestClient

from app.api.router import api_router
from app.api.v1.router import router as v1_router
from app.core.constants import API_PREFIX, OPENAPI_VERSION

# Every (method, path) in contract v0.2 rev 2 §2–§6, core and optional.
CONTRACT_ENDPOINTS: Final = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/ready"),
        ("GET", "/api/v1/districts"),
        ("GET", "/api/v1/expense-categories"),
        ("GET", "/api/v1/budget-benchmarks"),
        ("POST", "/api/v1/calculations/household-shock"),
        ("GET", "/api/v1/seasonal-swaps"),
        ("GET", "/api/v1/dashboard/filters"),
        ("GET", "/api/v1/dashboard/overview"),
        ("GET", "/api/v1/district-vulnerability"),
        ("GET", "/api/v1/district-vulnerability/{districtCode}"),
        ("POST", "/api/v1/calculations/policy-scenario"),
        ("GET", "/api/v1/methodology"),
        ("POST", "/api/v1/calculations/budget-comparison"),
        ("GET", "/api/v1/demo-household"),
    }
)
# Endpoints added beyond contract v0.2 at the project owner's request: official published
# statistics (FinScope 2026-10-26; EICV7 poverty and health insurance 2026-10-27). They are
# contract v0.3 (contract §10), agreed by the frontend teammate on 2026-10-27.
EXTENSION_ENDPOINTS: Final = frozenset(
    {
        ("GET", "/api/v1/nisr/sources"),
        ("GET", "/api/v1/nisr/financial-inclusion/national"),
        ("GET", "/api/v1/nisr/financial-inclusion/districts"),
        ("GET", "/api/v1/nisr/poverty"),
        ("GET", "/api/v1/nisr/health-insurance"),
        # Contract v0.4 (contract §11, from MISSING_APIS.pdf; frontend sign-off pending).
        ("GET", "/api/v1/shocks/catalog"),
        ("POST", "/api/v1/calculations/resilience-simulation"),
        ("POST", "/api/v1/calculations/agro-savings-projection"),
        ("POST", "/api/v1/calculations/stress-test"),
        ("GET", "/api/v1/calculations/district-comparison"),
        ("GET", "/api/v1/districts/{code}/basket-details"),
        # v0.4 content endpoints that answer `awaiting_validated_data` until a source exists.
        ("GET", "/api/v1/nutrition/indyo-yuzuye"),
        ("GET", "/api/v1/agro/harvest-calendar"),
        ("GET", "/api/v1/market/shopping-checklist"),
    }
)
# What this build ships. Optional endpoints not built: /methodology, /demo-household.
IMPLEMENTED_CONTRACT_ENDPOINTS: Final = CONTRACT_ENDPOINTS - {
    ("GET", "/api/v1/methodology"),
    ("GET", "/api/v1/demo-household"),
}
IMPLEMENTED_ENDPOINTS: Final = IMPLEMENTED_CONTRACT_ENDPOINTS | EXTENSION_ENDPOINTS
DOC_PATHS: Final = {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"}


def app_endpoints(app: FastAPI) -> set[tuple[str, str]]:
    """Effective (method, full path) pairs, as FastAPI matches them."""
    return {
        (method, context.path)
        for context in iter_route_contexts(app.routes)
        if context.path and context.path not in DOC_PATHS
        for method in (context.methods or set()) - {"HEAD"}
    }


def test_routes_equal_the_implemented_endpoints(stub_app: FastAPI) -> None:
    assert app_endpoints(stub_app) == IMPLEMENTED_ENDPOINTS


def test_every_shipped_route_is_in_the_contract_or_a_declared_extension() -> None:
    assert IMPLEMENTED_CONTRACT_ENDPOINTS <= CONTRACT_ENDPOINTS
    assert not EXTENSION_ENDPOINTS & CONTRACT_ENDPOINTS
    assert IMPLEMENTED_ENDPOINTS == IMPLEMENTED_CONTRACT_ENDPOINTS | EXTENSION_ENDPOINTS


def test_data_routes_carry_the_v1_prefix_exactly_once(stub_app: FastAPI) -> None:
    for _, path in app_endpoints(stub_app):
        if path in {"/health", "/ready"}:
            continue
        assert path.startswith(API_PREFIX + "/"), path
        assert path.count("/api/") == 1 and "/v1/v1" not in path, path
        assert "/v2" not in path


def test_v1_router_itself_has_no_prefix() -> None:
    assert v1_router.prefix == ""
    paths = [context.path or "" for context in iter_route_contexts(v1_router.routes)]
    assert paths and not any(path.startswith("/api") for path in paths)


def test_central_router_mounts_v1_once() -> None:
    v1_paths = [context.path or "" for context in iter_route_contexts(v1_router.routes)]
    mounted = [
        context.path or ""
        for context in iter_route_contexts(api_router.routes)
        if (context.path or "").startswith(API_PREFIX)
    ]
    assert len(mounted) == len(set(mounted)) == len(v1_paths)
    assert sorted(mounted) == sorted(f"{API_PREFIX}{path}" for path in v1_paths)


def test_openapi_versions_are_kept_separate(stub_app: FastAPI) -> None:
    schema = stub_app.openapi()
    assert schema["info"]["version"] == OPENAPI_VERSION == "0.2.0"
    assert "0.1" not in schema["info"]["version"]  # methodology version lives in `meta`
    assert all(path.startswith(("/api/v1/", "/health", "/ready")) for path in schema["paths"])


def test_openapi_declares_problem_json_errors_and_numeric_types(stub_app: FastAPI) -> None:
    schema = stub_app.openapi()
    shock = schema["paths"]["/api/v1/calculations/household-shock"]["post"]["responses"]
    assert "application/problem+json" in shock["422"]["content"]
    response = schema["components"]["schemas"]["HouseholdShockResponse"]["properties"]
    runway_types = {option.get("type") for option in response["runwayMonths"]["anyOf"]}
    assert runway_types == {"number", "null"}
    assert response["monthlyGap"]["type"] == "integer"
    weights = schema["components"]["schemas"]["Weights"]["properties"]
    assert weights["incomeInstability"]["type"] == "number"


def test_openapi_and_docs_are_served(client: TestClient) -> None:
    assert client.get("/openapi.json").status_code == 200
    docs = client.get("/docs")
    assert docs.status_code == 200 and "swagger" in docs.text.lower()


def test_cors_allows_the_vite_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/districts",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type,x-request-id",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in response.headers
    assert "X-Request-ID" in response.headers  # the preflight also carries a request ID


def test_cors_rejects_other_origins(client: TestClient) -> None:
    response = client.options(
        "/api/v1/districts",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in response.headers


def test_cors_exposes_the_request_id_on_simple_requests(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["access-control-expose-headers"] == "X-Request-ID"


def test_no_authentication_is_required(stub_app: FastAPI) -> None:
    schema = stub_app.openapi()
    assert "securitySchemes" not in schema.get("components", {})

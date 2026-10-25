"""Assertions shared by API tests (contract §1.3, §2.5–§2.7 of the implementation plan)."""

import json
from typing import Any, Final

import httpx2 as httpx

from app.core.constants import PROBLEM_TYPE_BASE

META: Final = {"isIllustrative": True, "methodologyVersion": "0.1"}

# Plan §2.5: raw query values that must be 422 `not_integer`.
NOT_INTEGER_QUERY_VALUES: Final = ("4.0", "4.5", "4e0", "%2B4", "-1", "%204", "0x4", "abc", "")
# Plan §2.6: JSON values that must be 422 `not_integer` in an integer body field.
NOT_INTEGER_BODY_VALUES: Final = ("180000", 1.5, 4.0, True, False)


def assert_problem(
    response: httpx.Response, status: int, slug: str, *errors: tuple[str, str]
) -> dict[str, Any]:
    """Status, media type, `type` slug and, when given, exactly these (field, code) errors."""
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    body: dict[str, Any] = response.json()
    assert body["type"] == PROBLEM_TYPE_BASE + slug
    assert body["status"] == status
    assert isinstance(body["title"], str) and isinstance(body["detail"], str)
    if errors:
        assert [(e["field"], e["code"]) for e in body["errors"]] == list(errors)
    allowed = {"type", "title", "status", "detail", "errors", "checks"}
    assert set(body) <= allowed
    return body


def raw_json(response: httpx.Response) -> Any:
    """Parse the raw text, so numeric types are what the wire carries (plan §2.7)."""
    return json.loads(response.text)


def assert_number(value: object, expected: float | int, *, integer: bool) -> None:
    assert not isinstance(value, str | bool), value
    if integer:
        assert isinstance(value, int), value
    else:
        assert isinstance(value, int | float), value
    assert value == expected

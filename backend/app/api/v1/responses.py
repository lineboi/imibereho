"""OpenAPI documentation of the contract §1.3 problem responses, per endpoint."""

from typing import Any, Final

from pydantic import BaseModel

from app.core.constants import PROBLEM_MEDIA_TYPE


class FieldErrorOut(BaseModel):
    field: str
    code: str
    message: str


class ProblemDetails(BaseModel):
    """RFC 9457 problem details (contract §1.3)."""

    type: str
    title: str
    status: int
    detail: str
    errors: list[FieldErrorOut] | None = None


_DESCRIPTIONS: Final = {
    400: "Malformed JSON (`malformed-request`) or an unknown query parameter (`unknown-parameter`)",
    404: "Unknown district (`district-not-found`) or no benchmark (`benchmark-not-available`)",
    422: "Field-level validation failure (`validation`)",
    500: "Unexpected error (`internal`); quote X-Request-ID when reporting",
}


def problem_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """`responses=` entries documenting each listed status as `application/problem+json`."""
    return {
        status: {
            "model": ProblemDetails,
            "description": _DESCRIPTIONS[status],
            "content": {PROBLEM_MEDIA_TYPE: {}},
        }
        for status in (*statuses, 500)
    }

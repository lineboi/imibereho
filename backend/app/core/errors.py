"""RFC 9457 problem details, exactly as contract §1.3 defines them.

Every problem body carries `type`, `title`, `status` and `detail`, plus `errors` on 400
`unknown-parameter` and 422, plus `checks` on 503 `not-ready`. Nothing else, and never any
internal detail.
"""

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, ClassVar, Final

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import iter_route_contexts
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse, Response
from starlette.routing import compile_path

from app.core.constants import PROBLEM_MEDIA_TYPE, PROBLEM_TYPE_BASE

logger = logging.getLogger("app.errors")


@dataclass(frozen=True, slots=True)
class FieldError:
    field: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"field": self.field, "code": self.code, "message": self.message}


def problem_body(
    slug: str,
    title: str,
    status: int,
    detail: str,
    *,
    errors: Sequence[FieldError] | None = None,
    checks: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "type": PROBLEM_TYPE_BASE + slug,
        "title": title,
        "status": status,
        "detail": detail,
    }
    if errors is not None:
        body["errors"] = [error.as_dict() for error in errors]
    if checks is not None:
        body["checks"] = dict(checks)
    return body


def problem_response(
    slug: str,
    title: str,
    status: int,
    detail: str,
    *,
    errors: Sequence[FieldError] | None = None,
    checks: Mapping[str, str] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        problem_body(slug, title, status, detail, errors=errors, checks=checks),
        status_code=status,
        media_type=PROBLEM_MEDIA_TYPE,
        headers=dict(headers) if headers else None,
    )


def internal_error_response() -> JSONResponse:
    return problem_response(
        "internal",
        "Internal server error",
        500,
        "An unexpected error occurred. Quote the X-Request-ID header when reporting it.",
    )


class ProblemError(Exception):
    """A domain error that maps to one contract §1.3 problem type."""

    slug: str = "internal"
    title: str = "Internal server error"
    status: int = 500
    headers: ClassVar[Mapping[str, str] | None] = None

    def __init__(self, detail: str, *, errors: Sequence[FieldError] | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.errors = errors


class DistrictNotFoundError(ProblemError):
    slug = "district-not-found"
    title = "District not found"
    status = 404

    def __init__(self) -> None:
        super().__init__("No district has this code.")


class BenchmarkNotAvailableError(ProblemError):
    slug = "benchmark-not-available"
    title = "Benchmark not available"
    status = 404

    def __init__(self) -> None:
        super().__init__("No benchmark exists for this district and household size.")


class SwapNotFoundError(ProblemError):
    slug = "swap-not-found"
    title = "Swap not found"
    status = 404

    def __init__(self) -> None:
        super().__init__("No seasonal swap has this id.")


class IdentifierTakenError(ProblemError):
    slug = "identifier-taken"
    title = "Identifier already registered"
    status = 409

    def __init__(self) -> None:
        super().__init__("An account with this identifier already exists. Log in instead.")


class InvalidCredentialsError(ProblemError):
    """The same answer for an unknown identifier and a wrong password (no account probing)."""

    slug = "invalid-credentials"
    title = "Invalid credentials"
    status = 401
    # RFC 9110 §15.5.2: a 401 names its authentication scheme.
    headers: ClassVar[Mapping[str, str] | None] = {"WWW-Authenticate": "Bearer"}

    def __init__(self) -> None:
        super().__init__("The identifier or password is incorrect.")


class NotAuthenticatedError(ProblemError):
    """A missing or unusable bearer token, whatever the reason (contract §11.8).

    One answer for a missing, malformed, wrongly signed or expired token and for an account
    that no longer exists, so a caller learns nothing about the token or the account.
    """

    slug = "not-authenticated"
    title = "Not authenticated"
    status = 401
    headers: ClassVar[Mapping[str, str] | None] = {"WWW-Authenticate": "Bearer"}

    def __init__(self) -> None:
        super().__init__("A valid bearer token is required.")


class AuthNotConfiguredError(ProblemError):
    slug = "auth-not-configured"
    title = "Accounts unavailable"
    status = 503

    def __init__(self) -> None:
        super().__init__("Accounts are not available on this server.")


class TransactionNotFoundError(ProblemError):
    """No transaction with this id belongs to the caller (another account's id included)."""

    slug = "transaction-not-found"
    title = "Transaction not found"
    status = 404

    def __init__(self) -> None:
        super().__init__("No transaction with this id exists in your tracker.")


class ResiliencePlanNotFoundError(ProblemError):
    """The caller has not saved a resilience plan (or deleted it)."""

    slug = "resilience-plan-not-found"
    title = "Resilience plan not found"
    status = 404

    def __init__(self) -> None:
        super().__init__("You have not saved a resilience plan.")


class IdempotencyKeyReusedError(ProblemError):
    slug = "idempotency-key-reused"
    title = "Idempotency key reused"
    status = 409

    def __init__(self) -> None:
        super().__init__(
            "This Idempotency-Key was already used for a different request. Use a new key."
        )


class RequestValidationProblem(ProblemError):
    """A 422 raised by a service, for rules that need reference data (validated before lookups)."""

    slug = "validation"
    title = "Invalid request"
    status = 422

    def __init__(self, errors: Sequence[FieldError]) -> None:
        super().__init__("One or more fields are invalid.", errors=errors)


# --- Mapping Pydantic error types onto contract error codes (plan A2 table) ---

_CODE_BY_TYPE: Final = {
    "missing": "required",
    "greater_than": "out_of_range",
    "greater_than_equal": "out_of_range",
    "less_than": "out_of_range",
    "less_than_equal": "out_of_range",
    "int_type": "not_integer",
    "int_parsing": "not_integer",
    "int_from_float": "not_integer",
    "not_integer": "not_integer",
    "out_of_range": "out_of_range",
    "enum": "unknown_value",
    "literal_error": "unknown_value",
    "unknown_value": "unknown_value",
    "string_too_long": "too_long",
    "extra_forbidden": "unknown_field",
    "required": "required",
    # Raised as PydanticCustomError types by the account (§11.8) and tracker (§11.10) schemas.
    "too_short": "too_short",
    "too_long": "too_long",
    "invalid_format": "invalid_format",
    "invalid_month": "invalid_format",
    "invalid_date": "invalid_format",
    "invalid_datetime": "invalid_format",
    "invalid_cursor": "invalid_format",
    "invalid_key": "invalid_format",
    "control_characters": "invalid_format",
    "category_mismatch": "unknown_value",
}
# A more precise message than the code's own, for error types that share a code.
_MESSAGE_BY_TYPE: Final = {
    "invalid_month": "Must be a month as YYYY-MM.",
    "invalid_date": "Must be a date as YYYY-MM-DD.",
    "invalid_datetime": (
        "Must be an ISO 8601 date-time with a time zone, e.g. 2026-10-26T14:30:00Z."
    ),
    "invalid_cursor": "Must be the nextCursor of a previous page.",
    "invalid_key": "Must be 1 to 64 printable ASCII characters.",
    "control_characters": "Must not contain control characters.",
    "category_mismatch": "This category does not belong to the transaction type.",
}

_MESSAGE_BY_CODE: Final = {
    "required": "This field is required.",
    "not_integer": "Must be a whole number.",
    "unknown_value": "This value is not allowed.",
    "too_long": "This value is too long.",
    "unknown_field": "This field is not recognised.",
    "too_short": "This value is too short.",
    "invalid_format": "Must be a +2507XXXXXXXX phone number or an email address.",
}


def _field_path(loc: Sequence[int | str]) -> str:
    """Contract §1.3: the camelCase dotted path to the field, without the `body`/`query` prefix."""
    sources = {"body", "query", "path", "header"}
    parts = [str(part) for part in loc[1:]] if loc and loc[0] in sources else []
    return ".".join(parts) if parts else str(loc[0]) if loc else ""


def _out_of_range_message(ctx: Mapping[str, Any] | None) -> str:
    if ctx is None:
        return "Value is out of range."
    if "ge" in ctx:
        return f"Must be at least {ctx['ge']}."
    if "le" in ctx:
        return f"Must be at most {ctx['le']}."
    if "gt" in ctx:
        return f"Must be greater than {ctx['gt']}."
    if "lt" in ctx:
        return f"Must be less than {ctx['lt']}."
    return "Value is out of range."


def map_validation_error(error: Mapping[str, Any]) -> FieldError:
    error_type = str(error.get("type", ""))
    loc = tuple(error.get("loc", ()))
    # `null` on a required field is reported as `required` (contract §1.2), whatever the type.
    code = "required" if error.get("input", ...) is None else _CODE_BY_TYPE.get(error_type)
    if code is None:
        # Any other shape problem (for example an object where a number is expected) is a bad
        # value. The contract's code list is closed, so `unknown_value` is the closest fit.
        code = "unknown_value"
    if code == "out_of_range":
        message = _out_of_range_message(error.get("ctx"))
    elif code != "required" and error_type in _MESSAGE_BY_TYPE:
        message = _MESSAGE_BY_TYPE[error_type]
    else:
        message = _MESSAGE_BY_CODE[code]
    return FieldError(field=_field_path(loc), code=code, message=message)


def _is_json_invalid(errors: Sequence[Mapping[str, Any]]) -> bool:
    return any(error.get("type") == "json_invalid" for error in errors)


async def request_validation_handler(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, RequestValidationError):  # registered for this type only
        raise exc
    raw_errors = exc.errors()
    if _is_json_invalid(raw_errors):
        return problem_response(
            "malformed-request", "Malformed request", 400, "The request body is not valid JSON."
        )
    unknown_query = [
        error
        for error in raw_errors
        if error.get("type") == "extra_forbidden" and tuple(error.get("loc", ()))[:1] == ("query",)
    ]
    if unknown_query:
        return problem_response(
            "unknown-parameter",
            "Unknown query parameter",
            400,
            "The request contains a query parameter this endpoint does not define.",
            errors=[map_validation_error(error) for error in unknown_query],
        )
    return problem_response(
        "validation",
        "Invalid request",
        422,
        "One or more fields are invalid.",
        errors=[map_validation_error(error) for error in raw_errors],
    )


async def problem_error_handler(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, ProblemError):  # registered for this type only
        raise exc
    return problem_response(
        exc.slug, exc.title, exc.status, exc.detail, errors=exc.errors, headers=exc.headers
    )


def _allowed_methods(request: Request) -> str | None:
    """Every method the path supports, for the 405 `Allow` header (RFC 9110 §15.5.6).

    Starlette lists only the first route that matches the path, so a path served by two routes
    (`GET` and `PATCH /user/profile`) would advertise one. This joins every effective route
    (included routers resolved to their full paths, as for the access-log templates) whose path
    matches the request.
    """
    path = request.url.path
    methods: set[str] = set()
    for context in iter_route_contexts(request.app.routes):
        if context.path and context.methods and compile_path(context.path)[0].match(path):
            methods.update(context.methods)
    return ", ".join(sorted(methods)) if methods else None


async def http_exception_handler(request: Request, exc: Exception) -> Response:
    if not isinstance(exc, StarletteHTTPException):  # registered for this type only
        raise exc
    if exc.status_code == 404:
        return problem_response("not-found", "Not found", 404, "No resource exists at this path.")
    if exc.status_code == 405:
        allow = _allowed_methods(request) or (exc.headers or {}).get("Allow")
        return problem_response(
            "method-not-allowed",
            "Method not allowed",
            405,
            "This path does not support the request method.",
            headers={"Allow": allow} if allow else None,
        )
    # No other HTTP exception is raised by this app; anything unexpected is a 500.
    logger.error("unexpected HTTP exception", extra={"status": exc.status_code})
    return internal_error_response()


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(ProblemError, problem_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

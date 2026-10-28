"""Household accounts: `POST /auth/register` and `POST /auth/login` (contract §11.8).

Field names and shapes follow MISSING_APIS.pdf page 4 exactly. The PDF gives no validation rules,
so the backend sets them (contract §11.8): the identifier is a Rwandan mobile number in E.164
form (+2507XXXXXXXX) or an ASCII email address; a password has 8 to 128 characters; the profile uses
the API's usual bounds; `currency` is RWF only; `preferredLanguage` is the frontend's EN or RW.
"""

import re
from typing import Annotated, Final, Literal

from pydantic import AfterValidator, Field, StrictInt, StrictStr
from pydantic_core import PydanticCustomError

from app.core.constants import HOUSEHOLD_SIZE_MAX, HOUSEHOLD_SIZE_MIN, MONEY_MAX
from app.schemas.common import ApiModel, BodyModel

PASSWORD_MIN_LENGTH: Final = 8
PASSWORD_MAX_LENGTH: Final = 128  # bounds the Argon2 work a single request can cause
IDENTIFIER_MAX_LENGTH: Final = 254  # the longest usable email address (RFC 5321 path limit)
TOKEN_TYPE: Final = "bearer"  # noqa: S105 (the token scheme, not a secret)

# ASCII only, by explicit character classes: `\d` and `\s` would also match Arabic-Indic digits,
# fullwidth characters and other Unicode lookalikes, letting one identifier be registered twice.
_ASCII_WHITESPACE: Final = " \t\n\r\f\v"
_PHONE: Final = re.compile(r"\+2507[0-9]{8}")
# Deliberately simple, not a full RFC 5322 parser: a local part of printable ASCII other than
# space and @, one @, and a domain of ASCII letters, digits and hyphens with at least one dot.
_EMAIL: Final = re.compile(r"[!-?A-~]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


def normalise_identifier(value: str) -> str:
    """A phone number as given (+2507XXXXXXXX), or an ASCII email address lower-cased.

    Only ASCII whitespace is trimmed from the ends. Anything else that is not ASCII, including
    invisible characters such as a zero-width space and fullwidth or non-Latin digits, is
    rejected rather than transformed, so two different strings never become one account.
    """
    candidate = value.strip(_ASCII_WHITESPACE)
    if _PHONE.fullmatch(candidate):
        return candidate
    if _EMAIL.fullmatch(candidate):
        return candidate.lower()
    raise PydanticCustomError(
        "invalid_format", "Must be a +2507XXXXXXXX phone number or an email address."
    )


def _password_long_enough(value: str) -> str:
    if len(value) < PASSWORD_MIN_LENGTH:
        raise PydanticCustomError("too_short", "This value is too short.")
    return value


Identifier = Annotated[
    StrictStr, Field(max_length=IDENTIFIER_MAX_LENGTH), AfterValidator(normalise_identifier)
]
Password = Annotated[
    StrictStr, Field(max_length=PASSWORD_MAX_LENGTH), AfterValidator(_password_long_enough)
]
PreferredLanguage = Literal["EN", "RW"]


class RegisterProfile(BodyModel):
    district: StrictStr = Field(max_length=32, description="A district code from /districts")
    household_size: Annotated[StrictInt, Field(ge=HOUSEHOLD_SIZE_MIN, le=HOUSEHOLD_SIZE_MAX)]
    monthly_income: Annotated[StrictInt, Field(ge=0, le=MONEY_MAX)]
    currency: Literal["RWF"]
    preferred_language: PreferredLanguage


class RegisterRequest(BodyModel):
    identifier: Identifier
    password: Password
    profile: RegisterProfile


class LoginRequest(BodyModel):
    # Not format-checked beyond its length: a malformed identifier simply matches no account,
    # and the answer is the same 401 as for a wrong password.
    identifier: Annotated[StrictStr, Field(max_length=IDENTIFIER_MAX_LENGTH)]
    password: Annotated[StrictStr, Field(max_length=PASSWORD_MAX_LENGTH)]


class RegisteredUser(ApiModel):
    id: str
    identifier: str
    district: str
    household_size: int


class RegisterResponse(ApiModel):
    token: str
    token_type: Literal["bearer"] = TOKEN_TYPE
    expires_in: int = Field(description="Seconds until the token expires")
    user: RegisteredUser


class LoggedInUser(ApiModel):
    id: str
    district: str


class LoginResponse(ApiModel):
    token: str
    token_type: Literal["bearer"] = TOKEN_TYPE
    user: LoggedInUser

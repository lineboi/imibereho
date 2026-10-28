"""Password hashing, account ids and bearer tokens for the account endpoints (contract §11.8).

- Passwords: Argon2id (argon2-cffi defaults, the RFC 9106 second recommended profile). Only the
  encoded hash is stored; a password is never stored, logged or returned.
- Account ids: "usr_" + a ULID (48-bit millisecond time + 80 random bits, Crockford base32), the
  form of the PDF's "usr_01JBCDEFGH" example.
- Tokens: JWT, HS256 (the PDF example's header), signed with JWT_SECRET_KEY, with `sub` (the
  account id), `iat` and `exp`; valid for TOKEN_TTL_SECONDS (the PDF's `expiresIn`: 86400).
  `verify_token` checks them strictly for the current-account dependency of protected routes.
"""

import re
import secrets
import time
from functools import cache
from typing import Final

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

TOKEN_TTL_SECONDS: Final = 86_400
TOKEN_ALGORITHM: Final = "HS256"  # noqa: S105 (an algorithm name, not a secret)
ACCOUNT_ID_PREFIX: Final = "usr_"
TRANSACTION_ID_PREFIX: Final = "tx_"
_CROCKFORD: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ACCOUNT_ID: Final = re.compile(r"usr_[0-9A-HJKMNP-TV-Z]{26}")

_hasher: Final = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


@cache
def _dummy_hash() -> str:
    # Verified against when no account matches, so a login for an unknown identifier costs the
    # same Argon2 work as one with a wrong password.
    return _hasher.hash(secrets.token_urlsafe(32))


def verify_password(password_hash: str | None, password: str) -> bool:
    """True only for a stored hash that matches. `None` (no account) still does the work."""
    try:
        return _hasher.verify(password_hash or _dummy_hash(), password) and bool(password_hash)
    except (VerificationError, InvalidHashError):
        return False


def ulid(now_ms: int | None = None, randomness: int | None = None) -> str:
    """26 Crockford base32 characters: 10 for the millisecond time, 16 for 80 random bits."""
    timestamp = time.time_ns() // 1_000_000 if now_ms is None else now_ms
    random_bits = secrets.randbits(80) if randomness is None else randomness
    value = (timestamp << 80) | random_bits
    return "".join(_CROCKFORD[(value >> shift) & 0x1F] for shift in range(125, -1, -5))


def new_account_id(now_ms: int | None = None, randomness: int | None = None) -> str:
    """'usr_' + a ULID."""
    return ACCOUNT_ID_PREFIX + ulid(now_ms, randomness)


def new_transaction_id() -> str:
    """'tx_' + a ULID (the form of the PDF's `tx_09JKA`; contract §11.10)."""
    return TRANSACTION_ID_PREFIX + ulid()


class InvalidTokenError(Exception):
    """Any token that must not authenticate. Deliberately carries no detail."""


def verify_token(token: str, secret: str, now: int | None = None) -> str:
    """The account id (`sub`) of a valid token, else `InvalidTokenError`.

    Valid means: a JWT signed with `secret` using HS256 only (the header's `alg` is never
    trusted, so `none` or another algorithm fails), with `sub`, `iat` and `exp` all present,
    `sub` an account id, `iat` and `exp` integers, `exp` in the future, `iat` not in the future
    and the lifetime no longer than TOKEN_TTL_SECONDS. No leeway is allowed.
    """
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[TOKEN_ALGORITHM],
            options={"require": ["sub", "iat", "exp"], "verify_iat": False, "verify_exp": False},
        )
    except jwt.PyJWTError:
        raise InvalidTokenError from None
    subject, issued_at, expires = claims["sub"], claims["iat"], claims["exp"]
    current = int(time.time()) if now is None else now
    if not (
        isinstance(subject, str)
        and _ACCOUNT_ID.fullmatch(subject)
        and type(issued_at) is int  # bool is an int subclass; a JSON true is not a time
        and type(expires) is int
        and issued_at <= current < expires
        and expires - issued_at <= TOKEN_TTL_SECONDS
    ):
        raise InvalidTokenError
    return subject


def issue_token(account_id: str, secret: str, now: int | None = None) -> str:
    issued_at = int(time.time()) if now is None else now
    claims = {"sub": account_id, "iat": issued_at, "exp": issued_at + TOKEN_TTL_SECONDS}
    return jwt.encode(claims, secret, algorithm=TOKEN_ALGORITHM)

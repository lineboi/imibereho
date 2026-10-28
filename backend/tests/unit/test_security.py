"""Password hashing, account ids and tokens for the account endpoints (contract §11.8)."""

import re
import warnings

import jwt
import pytest

from app.core.security import (
    TOKEN_TTL_SECONDS,
    InvalidTokenError,
    hash_password,
    issue_token,
    new_account_id,
    verify_password,
    verify_token,
)

SECRET = "unit-test-signing-key-0123456789abcdef"


def test_passwords_are_argon2id_salted_and_verify() -> None:
    first, second = hash_password("SecurePassword123!"), hash_password("SecurePassword123!")
    assert first.startswith("$argon2id$") and first != second  # a fresh salt each time
    assert verify_password(first, "SecurePassword123!")
    assert not verify_password(first, "securepassword123!")


def test_no_account_or_a_broken_hash_never_verifies() -> None:
    assert not verify_password(None, "SecurePassword123!")
    assert not verify_password("not-a-hash", "SecurePassword123!")


def test_account_ids_are_prefixed_ulids() -> None:
    assert new_account_id(0, 0) == "usr_" + "0" * 26
    assert new_account_id(1, 0) == "usr_" + "0" * 9 + "1" + "0" * 16
    assert new_account_id(0, 2**80 - 1) == "usr_" + "0" * 10 + "Z" * 16
    generated = new_account_id()
    assert re.fullmatch(r"usr_[0-9A-HJKMNP-TV-Z]{26}", generated)
    # Time-ordered: a later millisecond sorts later, whatever the randomness.
    assert new_account_id(2, 0) > new_account_id(1, 2**80 - 1)
    assert len({new_account_id() for _ in range(1_000)}) == 1_000


def test_tokens_carry_subject_issued_at_and_a_day_of_validity() -> None:
    token = issue_token("usr_X", SECRET, now=1_800_000_000)
    claims = jwt.decode(
        token, SECRET, algorithms=["HS256"], options={"verify_exp": False, "verify_iat": False}
    )
    assert claims == {"sub": "usr_X", "iat": 1_800_000_000, "exp": 1_800_000_000 + 86_400}
    assert TOKEN_TTL_SECONDS == 86_400


def test_expired_tokens_are_rejected() -> None:
    token = issue_token("usr_X", SECRET, now=1_000)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, SECRET, algorithms=["HS256"])


ACCOUNT = "usr_" + "0" * 10 + "Z" * 16
NOW = 1_800_000_000


def forged(claims: dict[str, object], key: str = SECRET, algorithm: str = "HS256") -> str:
    with warnings.catch_warnings():
        # The HS512 case reuses the HS256 test key on purpose; PyJWT warns that it is short.
        warnings.simplefilter("ignore", jwt.warnings.InsecureKeyLengthWarning)
        return jwt.encode(claims, key, algorithm=algorithm)


def test_verify_token_returns_the_subject_of_a_valid_token() -> None:
    assert verify_token(issue_token(ACCOUNT, SECRET, now=NOW), SECRET, now=NOW) == ACCOUNT
    # Valid until one second before `exp`, with no leeway.
    token = issue_token(ACCOUNT, SECRET, now=NOW)
    assert verify_token(token, SECRET, now=NOW + TOKEN_TTL_SECONDS - 1) == ACCOUNT
    with pytest.raises(InvalidTokenError):
        verify_token(token, SECRET, now=NOW + TOKEN_TTL_SECONDS)


VALID = {"sub": ACCOUNT, "iat": NOW, "exp": NOW + 60}


@pytest.mark.parametrize(
    "token",
    [
        "",
        "not-a-jwt",
        "a.b.c",
        forged(VALID, key="another-key-another-key-another-key"),  # wrong signature
        forged(VALID, algorithm="HS512"),  # right key, another algorithm
        jwt.encode(VALID, None, algorithm="none"),  # unsigned
        forged({"iat": NOW, "exp": NOW + 60}),  # no sub
        forged({"sub": ACCOUNT, "exp": NOW + 60}),  # no iat
        forged({"sub": ACCOUNT, "iat": NOW}),  # no exp
        forged({**VALID, "sub": "someone"}),  # not an account id
        forged({**VALID, "sub": 7}),
        forged({**VALID, "iat": float(NOW)}),  # times must be integers
        forged({**VALID, "exp": True}),
        forged({**VALID, "iat": "1800000000"}),
        forged({**VALID, "iat": NOW + 1}),  # issued in the future
        forged({**VALID, "exp": NOW}),  # expired at this second
        forged({**VALID, "exp": NOW + TOKEN_TTL_SECONDS + 1}),  # longer than a token lives
    ],
)
def test_verify_token_rejects_every_unusable_token(token: str) -> None:
    with pytest.raises(InvalidTokenError) as excinfo:
        verify_token(token, SECRET, now=NOW)
    # Nothing about the token, the secret or the cause travels with the error.
    assert str(excinfo.value) == "" and excinfo.value.__cause__ is None
    assert excinfo.value.__suppress_context__ or excinfo.value.__context__ is None

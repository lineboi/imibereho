"""uvicorn factories for the live-startup tests.

`build_stub`: the real app with a guarded `test` URL that is never contacted (no database needed).
`build_test_db`: the real app on TEST_DATABASE_URL with full startup verification.
"""

from fastapi import FastAPI

from app.core.config import load_settings
from app.core.logging import configure_logging
from app.main import create_app
from tests.conftest import make_settings


def build_stub() -> FastAPI:
    configure_logging("INFO")
    return create_app("test", settings=make_settings(), verify_database_on_startup=False)


def build_test_db() -> FastAPI:
    settings = load_settings()
    configure_logging("INFO")
    return create_app("test", settings=settings)

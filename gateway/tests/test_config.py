import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_production_requires_strong_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="short")


def test_production_requires_redis_and_disabled_docs():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="a" * 32, docs_enabled=False)

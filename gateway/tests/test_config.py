import pytest
from pydantic import ValidationError

from app.config.settings import Settings


def test_production_requires_strong_secret():
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="short")

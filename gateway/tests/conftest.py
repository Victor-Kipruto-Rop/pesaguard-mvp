import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test", allowed_hosts=["testserver"], rate_limit_requests=1000)


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as client:
        yield client

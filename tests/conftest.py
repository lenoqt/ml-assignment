import pytest

from app.config import GlobalConfig

@pytest.fixture
def global_config() -> GlobalConfig:
    return GlobalConfig()

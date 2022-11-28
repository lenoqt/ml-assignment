import pytest

from modules.config import GlobalConfig

@pytest.fixture
def global_config() -> GlobalConfig:
    return GlobalConfig()

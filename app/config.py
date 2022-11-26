import os
from dataclasses import dataclass
from typing import Optional, Union

from pydantic import BaseSettings, Field
from pydantic.networks import IPvAnyAddress
from pydantic.types import ConstrainedInt, SecretStr, conint

class Port(ConstrainedInt):
    port = conint(ge=0, le=65535)

class GlobalConfig(BaseSettings):
    ENV_STATE: Optional[str] = None
    APP_IPADDR: Optional[IPvAnyAddress] = None
    APP_PORT: Optional[Port] = None
    MINIO_ENDPOINT: Optional[str] = None
    MINIO_ACCESS_KEY: Optional[SecretStr] = None
    MINIO_SECRET_KEY: Optional[SecretStr] = None
    S3_BUCKET_NAME: Optional[str] = Field(default="ml_metadata")

    class Config:
        env_file: str = f"{os.getenv('PWD', '.')}/.env"

class DevConfig(GlobalConfig):
    class Config:
        env_prefix: str = "DEV_"

class StagingConfig(GlobalConfig):
    class Config:
        env_prefix: str = "STG_"

class ProdConfig(GlobalConfig):
    class Config:
        env_prefix: str = "PROD_"

@dataclass
class ConfigFactory:
    env_state: Optional[str]

    def get_config(self) -> Union[DevConfig, ProdConfig, StagingConfig]:
        match self.env_state:
            case "dev":
                return DevConfig()
            case "stg":
                return StagingConfig()
            case "prod":
                return ProdConfig()
            case _:
                raise ValueError(f"Env State not valid, got instead {self.env_state}")

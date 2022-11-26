from dataclasses import dataclass, field
from typing import Any, Optional
from transformers import PreTrainedTokenizer, PretrainedConfig
from .config import GlobalConfig, ConfigFactory
import uuid
import urllib3
import torch.nn as nn
import pickle
import logging
import io
from minio import Minio
from minio.error import S3Error


logger = logging.getLogger(__name__)
global_config = GlobalConfig()
app_config = ConfigFactory(global_config.ENV_STATE).get_config()
PART_SIZE = 10 * 1024 * 1024


@dataclass
class Model:
    name: str = field(init=False)
    model: nn.Module
    tokenizer: Optional[PreTrainedTokenizer] = None
    config: Optional[PretrainedConfig] = None
    metadata: dict = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    _client: Optional[Minio | None] = None
    _http_client: Optional[urllib3.ProxyManager | None] = None
    _uploaded: dict[str, bool] = field(default_factory=dict)
    _pickled_objs: dict = field(default_factory=dict)

    def __post_init__(self):
        if hasattr(self.model, "name_or_path"):
            self.name = (
                self.model.name_or_path + "_" + str(self.id)
            )  # pyright: ignore [reportGeneralTypeIssues]
        else:
            self.name = self.model.__class__.__name__ + "_" + str(self.id)

    def upload_to_minio_s3(self):

        bucket = app_config.S3_BUCKET_NAME

        if not self._client and not self._http_client:
            self._http_client = urllib3.ProxyManager(
                f"http://{app_config.MINIO_ENDPOINT}",
                timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
                retries=urllib3.Retry(
                    total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]
                ),
            )

            self._client = Minio(
                app_config.MINIO_ENDPOINT,
                access_key=app_config.MINIO_ACCESS_KEY.get_secret_value(),
                secret_key=app_config.MINIO_SECRET_KEY.get_secret_value(),
                http_client=self._http_client,
                secure=False,
            )
        found = self._client.bucket_exists(app_config.S3_BUCKET_NAME)
        if not found:
            logger.debug(f"Creating bucket: {bucket}..")
            self._client.make_bucket(app_config.S3_BUCKET_NAME)
        if not self._pickled_objs:
            logger.debug(
                f"Writing objects -> model: {self.model}, tokenizer: {self.tokenizer if not None else ''}, config: {self.config if not None else ''}"  # noqa: E501
            )
            self._pickled_objs["model"] = self._pickle_obj(self.model)
            if self.tokenizer:
                self._pickled_objs["tokenizer"] = self._pickle_obj(self.tokenizer)
            if self.config:
                self._pickled_objs["config"] = self._pickle_obj(self.config)
        # Start uploading to minio
        for key, value in self._pickled_objs.items():
            if not self._uploaded.get(key, None):
                try:
                    self.metadata[key] = self._client.put_object(
                        app_config.S3_BUCKET_NAME,
                        f"/models/{self.id}/{key}",
                        io.BytesIO(value),
                        length=-1,
                        part_size=PART_SIZE,
                    )
                    self._uploaded[key] = True
                except S3Error:
                    logger.error(f"An error has occurred trying to upload {key}")
                    self._uploaded[key] = False

    @staticmethod
    def _pickle_obj(obj: Any) -> bytes:
        return pickle.dumps(obj)

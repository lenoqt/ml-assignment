from dataclasses import dataclass, field
from typing import Any, Optional
from typing_extensions import Self
from transformers import PreTrainedTokenizer, PretrainedConfig
from transformers import M2M100Config, M2M100ForConditionalGeneration, M2M100Tokenizer
from .config import GlobalConfig, ConfigFactory
import uuid
import urllib3
import torch.nn as nn
import pickle
import logging
import io
import torch
from minio import Minio
from minio.deleteobjects import DeleteObject
from minio.error import S3Error


logger = logging.getLogger(__name__)
global_config = GlobalConfig()
app_config = ConfigFactory(global_config.ENV_STATE).get_config()
PART_SIZE = 10 * 1024 * 1024


def minio_client() -> Minio:
    http_client = urllib3.ProxyManager(
        f"http://{app_config.MINIO_ENDPOINT}",
        timeout=urllib3.Timeout.DEFAULT_TIMEOUT,
        retries=urllib3.Retry(
            total=3, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]
        ),
    )
    return Minio(
        app_config.MINIO_ENDPOINT,
        access_key=app_config.MINIO_ACCESS_KEY.get_secret_value(),
        secret_key=app_config.MINIO_SECRET_KEY.get_secret_value(),
        http_client=http_client,
        secure=False,
    )


@dataclass
class Model:
    # TODO: Change metadata dict to individual dict for easy retrieval of version_id
    name: str = field(init=False)
    model: nn.Module
    tokenizer: Optional[PreTrainedTokenizer] = None
    config: Optional[PretrainedConfig] = None
    metadata: dict = field(default_factory=dict)
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    _uploaded: dict[str, bool] = field(default_factory=dict)
    _pickled_objs: dict = field(default_factory=dict)

    def __post_init__(self):
        if hasattr(self.model, "name_or_path"):
            self.name = (
                str(self.model.name_or_path) + "_" + str(self.id)
            )  # pyright: ignore [reportGeneralTypeIssues]
        else:
            self.name = self.model.__class__.__name__ + "_" + str(self.id)

    def upload_to_minio_s3(self):
        client = minio_client()
        bucket = app_config.S3_BUCKET_NAME

        bucket_exists = client.bucket_exists(app_config.S3_BUCKET_NAME)
        if not bucket_exists:
            logger.debug(f"Creating bucket: {bucket}..")
            client.make_bucket(app_config.S3_BUCKET_NAME)
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
                    self.metadata[key] = client.put_object(
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

    @classmethod
    def from_minio_s3(
        cls, id: str, with_tokenizer: bool = False, with_config: bool = False
    ) -> Self:
        tokenizer = None
        config = None
        client = minio_client()
        bucket_exists = client.bucket_exists(app_config.S3_BUCKET_NAME)
        if not bucket_exists:
            raise
        model = cls._unpickle_obj(
            cls._get_object_from_minio(
                client, app_config.S3_BUCKET_NAME, f"models/{id}/model"
            )
        )
        if with_tokenizer is True:
            tokenizer = cls._unpickle_obj(
                cls._get_object_from_minio(
                    client, app_config.S3_BUCKET_NAME, f"models/{id}/tokenizer"
                )
            )
        if with_config is True:
            config = cls._unpickle_obj(
                cls._get_object_from_minio(
                    client, app_config.S3_BUCKET_NAME, f"models/{id}/config"
                )
            )
        return cls(
            id=uuid.UUID(id),
            model=model,
            tokenizer=tokenizer,
            config=config,
        )

    @classmethod
    def from_pretrained(cls, name: str) -> Self:
        model = M2M100ForConditionalGeneration.from_pretrained(name,
                                                               device_map=app_config.DEVICE,
                                                               load_in_8bit=False,
                                                               torch_dtype=torch.float16,
                                                               offload_folder="offload",
                                                               offload_state_dict=True)
        tokenizer = M2M100Tokenizer.from_pretrained(name)
        config = M2M100Config()
        return cls(model=model, tokenizer=tokenizer, config=config)

    def delete_from_minio_s3(self):
        if not all(self._uploaded):
            return
        client = minio_client()
        bucket = app_config.S3_BUCKET_NAME
        delete_object_list = map(
            lambda x: DeleteObject(x.object_name),
            client.list_objects(
                bucket_name=bucket,
                prefix=f"models/{self.id}",
                recursive=True
            )
        )
        errors = client.remove_objects(bucket, delete_object_list)
        for error in errors:
            logger.error(f"Error occurred deleting object {error}")
        for key, _ in self._uploaded.items():
            self._uploaded[key] = False

    @staticmethod
    def _get_object_from_minio(
        client: Minio, bucket: str, path: str, version: Optional[str] = None
    ) -> bytes:
        response = client.get_object(
            bucket,
            path,
            version,
        )
        byte_str = response.read()
        response.close()
        response.release_conn()
        return byte_str

    @staticmethod
    def _pickle_obj(obj: Any) -> bytes:
        return pickle.dumps(obj)

    @staticmethod
    def _unpickle_obj(obj: bytes) -> Any:
        return pickle.loads(obj)

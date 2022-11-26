from app.config import ConfigFactory

def test_config(global_config):
    dev_config = ConfigFactory(global_config.ENV_STATE).get_config()
    assert global_config.ENV_STATE
    assert dev_config.MINIO_ENDPOINT
    assert dev_config.MINIO_ACCESS_KEY.get_secret_value() != None
    assert dev_config.MINIO_SECRET_KEY.get_secret_value() != None
    assert dev_config.S3_BUCKET_NAME
    assert dev_config.APP_IPADDR.compressed
    assert dev_config.APP_PORT


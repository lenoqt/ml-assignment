from app.config import ConfigFactory

def test_config(global_config):
    dev_config = ConfigFactory(global_config.ENV_STATE).get_config()
    assert global_config.ENV_STATE == 'dev'
    assert dev_config.MINIO_IP.compressed == '127.0.0.1'
    assert dev_config.MINIO_PORT == 9999
    assert dev_config.MINIO_PASSWORD.get_secret_value() == "minio123"
    assert dev_config.APP_IPADDR.compressed == '127.0.0.1'
    assert dev_config.APP_PORT == 8888



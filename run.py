from modules.config import GlobalConfig, ConfigFactory
import logging
import uvicorn
import asyncio

logger = logging.getLogger(__name__)
global_config = GlobalConfig()
app_config = ConfigFactory(global_config.ENV_STATE).get_config()


async def main():
    logger.info(f"Starting serving at {app_config.APP_IPADDR}:{app_config.APP_PORT}")
    
    config = uvicorn.Config(
        "modules.app:app",
        host=app_config.APP_IPADDR.compressed,
        port=app_config.APP_PORT,
        reload=True,
        reload_dirs=["modules"]
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())

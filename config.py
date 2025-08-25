import logging

from pydantic_settings import BaseSettings 

logging.basicConfig(
    format="%(levelname)s: %(asctime)s: %(message)s",
    filename="logs/logs.txt",
    level=logging.INFO,
)

logging.getLogger("uvicorn.access").disabled = True

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.getLevelName(logging.DEBUG))


class Settings(BaseSettings):
    DEBUG: bool
    REPO_PATH: str
    MAIN_BRANCH: str


settings = Settings(_env_file=".env")

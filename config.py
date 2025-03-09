import logging
from typing import Optional
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
    DEBUG: bool = True
    REPO_PATH: Optional[str] = None
    MAIN_BRANCH: str = "master"


settings = Settings(_env_file=".env", _env_file_encoding="utf-8")

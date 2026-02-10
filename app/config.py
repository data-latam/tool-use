from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    tools_dir: Path = Path("tools")
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class PlatformSettings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment: Environment = "development"
    workspace_root: Path = Field(default=Path("workspace"))
    database_url: str = "sqlite:///workspace/synaisthesis.db"
    artifact_root: Path = Field(default=Path("workspace/artifacts"))
    log_level: LogLevel = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid")

    platform: PlatformSettings

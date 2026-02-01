from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS Origins (comma-separated string)
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Task Configuration
    max_sample_count: int = 4
    default_sample_count: int = 1

    # PPTAgent Configuration
    pptagent_workspace: str = "/workspace"
    pptagent_docker_url: str = "http://deeppresenter-host:7861"
    pptagent_mode: str = "auto"  # local, docker, auto

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS origins string to list"""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return [self.cors_origins]


settings = Settings()

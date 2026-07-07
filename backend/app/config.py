from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field("Dockerized Microservices API", validation_alias="APP_NAME")
    environment: str = Field("local", validation_alias="ENVIRONMENT")
    database_url: str = Field(
        "postgresql://app_user:change_me@postgres:5432/app_db",
        validation_alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://redis:6379/0", validation_alias="REDIS_URL")
    allowed_origins: str = Field(
        "http://localhost:3000,http://localhost:8000",
        validation_alias="ALLOWED_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()

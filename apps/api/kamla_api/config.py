from pydantic_settings import BaseSettings, SettingsConfigDict


def sqlalchemy_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    app_database_url: str
    clerk_issuer: str
    clerk_audience: str
    clerk_jwks_url: str
    cors_origins: str = "http://localhost:3000"

    @property
    def sqlalchemy_database_url(self) -> str:
        return sqlalchemy_url(self.database_url)

    @property
    def sqlalchemy_app_database_url(self) -> str:
        return sqlalchemy_url(self.app_database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


def get_settings() -> Settings:
    return Settings()

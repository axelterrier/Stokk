from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "openfoodfacts"
    MONGO_COLLECTION: str = "products"
    SECRET_KEY: str = "changeme"
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


settings = Settings()

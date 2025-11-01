from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Cosmetic Shop API"
    APP_VERSION: str = "1.0.0"
    APP_DEBUG: bool = True

    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # Defaults optimized for Docker compose; override via .env in local/dev as needed
    # MONGODB_URI: str = "mongodb://mongodb:27017/cosmetic_shop_db"
    MONGODB_URI: str
    MONGODB_DB: str = "cosmetic_shop_db"

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Accept unknown env vars (e.g., db_user, db_password) without failing
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    compose_project_name: str | None = None


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "AtelierAranier API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://atelier_user:atelier_pass@db:5432/atelieraranier"

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    GOOGLE_CLIENT_ID: str = ""

    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@atelieraranier.com"
    SMTP_USE_TLS: bool = False


settings = Settings()

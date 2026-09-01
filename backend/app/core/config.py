import json

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ORIGINS = ["http://localhost:4200", "http://127.0.0.1:4200"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "AtelierAranier API"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql://atelier_user:atelier_pass@db:5432/atelieraranier"

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    # str (no list[str]): asi pydantic-settings no intenta json.loads() el
    # valor crudo de la env var antes de que lleguemos a parsearlo nosotros.
    # Tolerante con como se escriba en paneles como Render: JSON
    # ("[\"a\",\"b\"]"), texto separado por comas ("a,b"), o vacio (default).
    BACKEND_CORS_ORIGINS: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        value = self.BACKEND_CORS_ORIGINS.strip()
        if not value:
            return DEFAULT_CORS_ORIGINS
        if value.startswith("["):
            return json.loads(value)
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    GOOGLE_CLIENT_ID: str = ""

    SMTP_HOST: str = "mailpit"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@atelieraranier.com"
    SMTP_USE_TLS: bool = False


settings = Settings()

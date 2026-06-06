import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neon DB
    database_url: str = ""

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24  # 24 hours

    # Encryption
    fernet_key: str = ""

    # Existing server settings
    gemini_api_key: str = ""
    proxy: str = ""
    host: str = "0.0.0.0"
    port: int = 3897

    # Backward compatibility: when true, /v1/* works without JWT using the global client
    disable_auth: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",  # Allow .env vars not in model (e.g., SECURE_1PSID)
    }


settings = Settings()

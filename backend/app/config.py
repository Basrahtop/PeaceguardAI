from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "PeaceGuard AI"
    API_V1_STR: str = "/api/v1"
    
    # GOOGLE_APPLICATION_CREDENTIALS environment variable will be used by Google Cloud client libraries.
    # No need to define it here explicitly if it's set in your environment.

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()
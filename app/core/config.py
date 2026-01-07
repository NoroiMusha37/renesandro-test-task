import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ELEVENLABS_API_KEY: str

    TEMP_DIR: str = "/tmp"
    MAX_DOWNLOAD_WORKERS: int = 10
    CHUNK_SIZE: int = 16384

    GCS_BUCKET_NAME: str
    GCS_SERVICE_ACCOUNT_JSON: str

    @property
    def gcs_credentials(self):
        try:
            return json.loads(self.GCS_SERVICE_ACCOUNT_JSON)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid GCS credentials: {e}")

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

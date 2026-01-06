from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ELEVENLABS_API_KEY: str

    TEMP_DIR: str = "/tmp"
    MAX_DOWNLOAD_WORKERS: int = 10
    CHUNK_SIZE: int = 16384

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

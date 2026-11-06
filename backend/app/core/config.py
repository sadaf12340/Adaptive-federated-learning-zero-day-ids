from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    database_url: str = f"sqlite:///{BASE_DIR / 'adaptive_ids.db'}"
    upload_dir: str = str(BASE_DIR.parent / 'data' / 'generated')
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', extra='ignore')

settings = Settings()

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # .env holds the deployed configuration; .env.local overrides it for local work.
    model_config = SettingsConfigDict(env_file=(".env", ".env.local"), extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:pawcare@localhost:5433/pawcare"
    supabase_url: str = "http://localhost:54321"
    supabase_jwt_aud: str = "authenticated"
    supabase_jwt_secret: str = ""
    whatsapp_token: str = ""
    whatsapp_app_secret: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_mode: str = "demo"
    whatsapp_verify_token: str = "pawcare-demo-verify"
    public_base_url: str = "http://localhost:3000"
    # Keyless room provider for demos. Swap for a managed video provider before launch.
    video_base_url: str = "https://meet.jit.si"
    cron_secret: str = "dev-cron-secret"
    # Where parents' uploaded paper records land. Object storage replaces this later.
    record_storage_dir: str = "var/legacy-records"
    environment: str = "development"

    @property
    def is_local_database(self) -> bool:
        return "localhost" in self.database_url or "127.0.0.1" in self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()

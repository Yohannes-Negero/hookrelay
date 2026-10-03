from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "hookrelay"
    admin_token: str = "change-me"
    stripe_webhook_secret: str = ""

    def webhook_secret_for(self, provider: str) -> str:
        return {"stripe": self.stripe_webhook_secret}.get(provider, "")


@lru_cache
def get_settings() -> Settings:
    return Settings()

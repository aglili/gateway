import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    arkesel_api_key: str = os.getenv("ARKESEL_API_KEY")
    arkesel_api_url: str = os.getenv("ARKESEL_API_URL", "https://sms.arkesel.com")
    mnotify_api_key: str = os.getenv("MNOTIFY_API_KEY")
    mnotify_api_url: str = os.getenv("MNOTIFY_API_URL", "https://api.mnotify.com")
    arkesel_sender_id: str = os.getenv("ARKESEL_SENDER_ID")
    mnotify_sender_id: str = os.getenv("MNOTIFY_SENDER_ID")

    application_name: str = "SMS Gateway with Circuit Breaker"
    api_version: str = "1.0.0"
    api_docs_url: str = "/docs"

    failure_threshold: int = 2
    reset_timeout: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings():
    return Settings()


settings = get_settings()

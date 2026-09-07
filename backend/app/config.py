import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_URL: str = os.getenv("DB_URL", "postgresql+asyncpg://user:password@localhost/dbname")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "insecure-default-for-development")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "insecure-refresh-default")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    TOKEN_EXPIRE_MINUTES: int = int(os.getenv("TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))
    REFRESH_ALGORITHM: str = os.getenv("REFRESH_ALGORITHM", "HS256")


settings = Settings()

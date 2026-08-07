import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/edcrms"
    SECRET_KEY: str = "change_this_super_secret_key_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    PROJECT_NAME: str = "Enterprise Data Center Rack Management System"

    # SMTP / Email notification settings
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@edcrms.com"
    SMTP_USE_TLS: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

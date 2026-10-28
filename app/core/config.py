import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30

    STRIPE_SECRET_KEY: str = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_BASIC: str = os.environ.get("STRIPE_PRICE_BASIC", "")
    STRIPE_PRICE_PREMIUM: str = os.environ.get("STRIPE_PRICE_PREMIUM", "")

    FRONTEND_URL: str = os.environ.get("FRONTEND_URL", "https://nossahistoria.netlify.app")

    CLOUDINARY_CLOUD_NAME: str = os.environ.get("CLOUDINARY_CLOUD_NAME", "duknkjihr")
    CLOUDINARY_UPLOAD_PRESET: str = os.environ.get("CLOUDINARY_UPLOAD_PRESET", "nossa-historia")

    ADMIN_TOKEN: str = os.environ.get("ADMIN_TOKEN", "nossahistoria-admin-2026")

    class Config:
        env_file = ".env"


settings = Settings()

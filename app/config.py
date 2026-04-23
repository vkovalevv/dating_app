from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

    REDIS_HOST: str
    REDIS_PORT: int
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # S3
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str

    SENDER_USERNAME: str
    SENDER_PASSWORD: str

    RECEIVER_USERNAME: str
    RECEIVER_PASSWORD: str

    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_BACKEND_URL: str = "redis://redis:6379/1"

    class Config:
        env_file = ".env"


settings = Settings()

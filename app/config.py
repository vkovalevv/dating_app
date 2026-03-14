from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

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

    class Config:
        env_file = ".env"


settings = Settings()

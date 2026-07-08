import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://rateshield:rateshield@localhost:3306/rateshield",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

    DEFAULT_RATE_LIMIT_ALGORITHM = os.getenv("DEFAULT_RATE_LIMIT_ALGORITHM", "fixed_window")
    DEFAULT_MAX_REQUESTS = int(os.getenv("DEFAULT_MAX_REQUESTS", "100"))
    DEFAULT_TIME_WINDOW = int(os.getenv("DEFAULT_TIME_WINDOW", "60"))
    DEFAULT_REFILL_RATE = float(os.getenv("DEFAULT_REFILL_RATE", "10"))
    DEFAULT_BUCKET_CAPACITY = int(os.getenv("DEFAULT_BUCKET_CAPACITY", "100"))

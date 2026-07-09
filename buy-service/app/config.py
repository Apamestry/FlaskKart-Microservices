import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET = os.getenv("JWT_SECRET")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    VIEW_SERVICE_URL = os.getenv("VIEW_SERVICE_URL")
    CART_SERVICE_URL = os.getenv("CART_SERVICE_URL")

    @staticmethod
    def validate():
        required = [
            "SECRET_KEY", "JWT_SECRET",
            "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME",
            "VIEW_SERVICE_URL", "CART_SERVICE_URL",
        ]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Check your .env file."
            )
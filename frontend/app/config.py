import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    GATEWAY_URL = os.getenv("GATEWAY_URL")

    @staticmethod
    def validate():
        required = ["SECRET_KEY", "GATEWAY_URL"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}. "
                "Check your .env file."
            )
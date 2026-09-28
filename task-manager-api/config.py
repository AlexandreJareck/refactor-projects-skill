import os


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TASK_MANAGER_DATABASE_URI", "sqlite:///tasks.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("TASK_MANAGER_SECRET_KEY")
    DEBUG = os.getenv("TASK_MANAGER_DEBUG", "false").lower() in {
        "1",
        "true",
        "yes",
    }


def validate_config(config):
    secret_key = config.get("SECRET_KEY")
    if not isinstance(secret_key, str) or len(secret_key) < 32:
        raise RuntimeError(
            "TASK_MANAGER_SECRET_KEY is required and must contain at least 32 characters"
        )


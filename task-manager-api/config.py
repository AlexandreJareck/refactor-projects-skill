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


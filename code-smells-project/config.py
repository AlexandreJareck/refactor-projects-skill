"""External configuration for the store API."""

import os


def load_config():
    return {
        "DATABASE": os.environ.get("LOJA_DATABASE", "loja.db"),
        "SECRET_KEY": os.environ.get("LOJA_SECRET_KEY"),
        "DEBUG": os.environ.get("LOJA_DEBUG", "0") == "1",
    }


def server_config():
    return {
        "host": os.environ.get("LOJA_HOST", "0.0.0.0"),
        "port": int(os.environ.get("LOJA_PORT", "5000")),
    }

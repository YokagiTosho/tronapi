import os


from dataclasses import dataclass
from typing import Optional
from collections.abc import Callable
from functools import wraps

@dataclass
class Config:
    api_key: str
    db_addr: str


def cache_config(get_cfg: Callable[[], Config]):
    cached: Optional[Config] = None

    @wraps(get_cfg)
    def wrapper() -> Config:
        nonlocal cached

        if cached is None:
            cached = get_cfg()

        return cached

    return wrapper


@cache_config
def get_config() -> Config:
    API_KEY: Optional[str] = os.getenv("API_KEY", None)
    if not API_KEY:
        raise ValueError("'API_KEY' is not specified in environment variable")

    POSTGRES_USER = os.getenv("POSTGRES_USER", None)
    if POSTGRES_USER is None:
        raise ValueError("'POSTGRES_USER'  is not specified in environment variable")

    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", None)
    if POSTGRES_PASSWORD is None:
        raise ValueError("'POSTGRES_PASSWORD' is not specified in environment variable")

    DBADDR: str = os.getenv("DBADDR", default="postgres:5432")

    full_db_path = f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DBADDR}"

    return Config(api_key=API_KEY, db_addr=full_db_path)

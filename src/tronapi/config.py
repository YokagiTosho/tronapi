import os

from dataclasses import dataclass
from typing import Optional

from tronapi.utils import cache


@dataclass
class Config:
    api_key: str
    db_addr: str


@cache
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

import os
import sys

from dataclasses import dataclass
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tronpy import AsyncTron
from tronpy.providers import AsyncHTTPProvider

from typing import Optional

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from sqlalchemy import DECIMAL, Integer, String
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


@dataclass
class Config:
    api_key: str
    db_addr: str


def init_env() -> Config:
    API_KEY: Optional[str] = os.getenv("API_KEY", None)
    if API_KEY is None:
        sys.stderr.write("'API_KEY' is not specified")
        sys.exit(1)

    POSTGRES_USER = os.getenv("POSTGRES_USER", None)
    if POSTGRES_USER is None:
        sys.stderr.write("'POSTGRES_USER'  is not specified")
        sys.exit(1)

    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", None)
    if POSTGRES_PASSWORD is None:
        sys.stderr.write("'POSTGRES_PASSWORD' is not specified")
        sys.exit(1)

    DBADDR: str = os.getenv("DBADDR", default="postgres:5432")

    full_db_path = f"{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DBADDR}"

    return Config(api_key=API_KEY, db_addr=full_db_path)


class Base(DeclarativeBase):
    pass


class WalletInfo(Base):
    __tablename__ = "wallet_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    address: Mapped[str] = mapped_column(String(100))

    energy: Mapped[int] = mapped_column(Integer)
    bandwidth: Mapped[int] = mapped_column(Integer)
    balance: Mapped[int] = mapped_column(DECIMAL)


config = init_env()

engine = create_async_engine(f"postgresql+asyncpg://{config.db_addr}", echo=True)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine)

tron_provider = AsyncHTTPProvider(api_key=config.api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/get_last_records/")
async def get_last_records(page: int = 1):
    if page < 1:
        return None

    limit = 10

    offset = (page-1)*limit

    async with async_session() as session:
        query = select(WalletInfo).offset(offset).limit(limit)
        result = await session.execute(query)

        out = []
        for scalar in result.scalars():
            out.append({
                "address": scalar.address,
                "account_info": {
                    "energy": scalar.energy,
                    "bandwidth": scalar.bandwidth,
                    "trx balance": scalar.balance,
                },
            })

    return out


@app.post("/wallet/")
async def wallet_information(address: str):
    async with AsyncTron(tron_provider) as client:
        energy = await client.get_energy(address)
        bandwidth = await client.get_bandwidth(address)
        balance = await client.get_account_balance(address)

    async with async_session() as session:
        async with session.begin():
            session.add(WalletInfo(
                address=address,
                energy=energy,
                bandwidth=bandwidth,
                balance=balance
            ))
            await session.commit()

    return {
        "address": address,
        "account_info": {
            "energy": energy,
            "bandwidth": bandwidth,
            "trx balance": balance,
        },
    }

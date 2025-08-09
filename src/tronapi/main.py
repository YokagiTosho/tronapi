from contextlib import asynccontextmanager
from decimal import Decimal

import sqlalchemy
import tronpy.exceptions as tron_exc
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from tronpy import AsyncTron
from tronpy.providers import AsyncHTTPProvider

from tronapi.config import Config, get_config


class AccounInfoModel(BaseModel):
    energy: int
    bandwidth: int
    balance: Decimal


class WalletInfoModel(BaseModel):
    address: str
    row_created_at: str
    account_info: AccounInfoModel


class Base(DeclarativeBase):
    pass


class WalletInfo(Base):
    __tablename__ = "wallet_info"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(100))

    energy: Mapped[int] = mapped_column(Integer)
    bandwidth: Mapped[int] = mapped_column(Integer)
    balance: Mapped[Decimal] = mapped_column(sqlalchemy.DECIMAL)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )


config: Config = get_config()

engine = create_async_engine(f"postgresql+asyncpg://{config.db_addr}", echo=True)

async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def get_tron_provider(config: Config = Depends(get_config)):
    return AsyncHTTPProvider(api_key=config.api_key)


async def get_tron(provider: AsyncHTTPProvider = Depends(get_tron_provider)):
    async with AsyncTron(provider) as client:
        yield client


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/records/")
async def records(
    page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)
) -> list[WalletInfoModel]:

    offset = (page - 1) * limit

    async with async_session() as session:
        try:
            query = (
                select(WalletInfo)
                .order_by(WalletInfo.id.desc())
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(query)

            out: list[WalletInfoModel] = []

            for r in result.scalars().all():
                out.append(
                    WalletInfoModel(
                        address=r.address,
                        row_created_at=str(r.created_at),
                        account_info=AccounInfoModel(
                            energy=r.energy, bandwidth=r.bandwidth, balance=r.balance
                        ),
                    )
                )
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Internal server error")

    return out


@app.post("/wallet/")
async def wallet_information(
    address: str, tron: AsyncTron = Depends(get_tron)
) -> WalletInfoModel:
    try:
        energy: int = await tron.get_energy(address)
        bandwidth: int = await tron.get_bandwidth(address)
        balance: Decimal = await tron.get_account_balance(address)
    except tron_exc.AddressNotFound:
        raise HTTPException(status_code=400, detail="Address not found")
    except tron_exc.BadAddress:
        raise HTTPException(status_code=400, detail="Bad address")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Bad request")

    async with async_session() as session:
        async with session.begin():
            try:
                wallet_info = WalletInfo(
                    address=address, energy=energy, bandwidth=bandwidth, balance=balance
                )
                session.add(wallet_info)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error")

        return WalletInfoModel(
            address=address,
            row_created_at=str(wallet_info.created_at),
            account_info=AccounInfoModel(
                energy=energy, bandwidth=bandwidth, balance=balance
            ),
        )

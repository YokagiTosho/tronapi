from contextlib import asynccontextmanager
from decimal import Decimal

import tronpy.exceptions as tron_exc
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel

from tronpy import AsyncTron
from tronpy.providers import AsyncHTTPProvider

from tronapi.config import Config, get_config

from tronapi.orm import Base, WalletInfo
from tronapi.orm import get_async_engine, get_async_sessionmaker

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine


class AccountInfoModel(BaseModel):
    energy: int
    bandwidth: int
    balance: Decimal


class WalletInfoModel(BaseModel):
    address: str
    row_created_at: str
    account_info: AccountInfoModel


async def get_tron_provider(config: Config = Depends(get_config)):
    return AsyncHTTPProvider(api_key=config.api_key)


async def get_tron(provider: AsyncHTTPProvider = Depends(get_tron_provider)):
    async with AsyncTron(provider) as client:
        yield client


@asynccontextmanager
async def lifespan(_: FastAPI):
    engine: AsyncEngine = get_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/records/")
async def records(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    async_session=Depends(get_async_sessionmaker),
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
                        account_info=AccountInfoModel(
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
    address: str,
    tron: AsyncTron = Depends(get_tron),
    async_session=Depends(get_async_sessionmaker),
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

                await session.commit()

            except Exception as e:
                print(e)
                raise HTTPException(status_code=500, detail="Internal server error")

        return WalletInfoModel(
            address=address,
            row_created_at=str(wallet_info.created_at),
            account_info=AccountInfoModel(
                energy=energy, bandwidth=bandwidth, balance=balance
            ),
        )

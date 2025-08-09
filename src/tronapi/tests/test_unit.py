import pytest

from decimal import Decimal
from tronapi.config import Config, get_config
from sqlalchemy import select

from tronapi.orm import get_async_sessionmaker, WalletInfo

from datetime import datetime

@pytest.mark.asyncio
async def test_wallet_info_db_insert():

    test_data = {
        "address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "energy": 150,
        "bandwidth": 300,
        "balance": Decimal("123.45")
    }

    async_session = get_async_sessionmaker()

    wallet_info = WalletInfo(
        **test_data
    )

    async with async_session() as session:
        async with session.begin():

            session.add(wallet_info)
            await session.commit()

        session.refresh(wallet_info)

        assert wallet_info.address == test_data["address"]
        assert wallet_info.energy == test_data["energy"]
        assert wallet_info.bandwidth == test_data["bandwidth"]
        assert wallet_info.balance == test_data["balance"]

        assert isinstance(wallet_info.created_at, datetime)


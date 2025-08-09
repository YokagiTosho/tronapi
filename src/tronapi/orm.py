import sqlalchemy
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncEngine

from decimal import Decimal

from tronapi.utils import cache
from tronapi.config import get_config, Config


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


@cache
def get_async_engine() -> AsyncEngine:
    cfg: Config = get_config()

    engine: AsyncEngine = create_async_engine(
        f"postgresql+asyncpg://{cfg.db_addr}"
    )

    return engine


@cache
def get_async_sessionmaker() -> async_sessionmaker[AsyncSession]:
    engine = get_async_engine()

    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    return async_session

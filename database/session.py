from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from config import db_settings


# sqlite
# engine = create_engine(
#     url="sqlite:///data.db", echo=True, connect_args={"check_same_thread": False}
# )

engine = create_async_engine(url=db_settings.POSTGRES_URL, echo=True)


async def create_db_tables():
    async with engine.begin() as conn:
        # creating tables for db
        from database.models import Shipment, Seller

        await conn.run_sync(SQLModel.metadata.create_all)


async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session():
    async with async_session() as session:
        yield session

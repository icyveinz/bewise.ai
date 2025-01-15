import asyncio
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from models import Base

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/applications_db"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    retries = 10
    while retries > 0:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database initialized successfully")
            break
        except OperationalError as e:
            if "the database system is starting up" in str(e):
                print("Database is not ready yet. Retrying...")
                retries -= 1
                await asyncio.sleep(3)  # Wait for 3 seconds before retrying
            else:
                raise e
    if retries == 0:
        raise RuntimeError("Failed to initialize the database after multiple retries")

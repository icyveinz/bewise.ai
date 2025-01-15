from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError
import asyncio

DATABASE_URL = "postgresql+asyncpg://user:password@db:5432/applications_db"

engine = create_async_engine(DATABASE_URL)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

async def init_db():
    retries = 20
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
                await asyncio.sleep(5)  # Increase sleep time
            else:
                print(f"Unexpected error: {e}")
                raise e
    if retries == 0:
        raise RuntimeError("Failed to initialize the database after multiple retries")
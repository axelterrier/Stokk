from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pymongo import MongoClient
from app.core.config import settings

# ── PostgreSQL ────────────────────────────────────────────────────────────────

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Crée les tables si elles n'existent pas encore."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── MongoDB ───────────────────────────────────────────────────────────────────

_mongo_client: MongoClient | None = None


def get_mongo_collection():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    db = _mongo_client[settings.MONGO_DB]
    return db[settings.MONGO_COLLECTION]

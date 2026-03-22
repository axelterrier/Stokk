"""Migration : ajout colonne quantity_str sur products"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def migrate():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        print("Adding quantity_str column to products...")
        await conn.execute(text("""
            ALTER TABLE products
            ADD COLUMN IF NOT EXISTS quantity_str VARCHAR(50)
        """))
        print("Done.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())

"""
Migration : ajout table locations + refactoring location dans stock_items
Run: python migrate_locations.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def migrate():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        print("Creating locations table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS locations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL,
                parent_id UUID REFERENCES locations(id) ON DELETE SET NULL,
                color VARCHAR(20)
            )
        """))

        print("Adding location_id column to stock_items...")
        await conn.execute(text("""
            ALTER TABLE stock_items
            ADD COLUMN IF NOT EXISTS location_id UUID REFERENCES locations(id) ON DELETE SET NULL
        """))

        print("Dropping old location text column...")
        await conn.execute(text("""
            ALTER TABLE stock_items
            DROP COLUMN IF EXISTS location
        """))

        print("Done.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate())

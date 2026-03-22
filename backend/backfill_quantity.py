"""
Backfill quantity_str pour les produits en cache PG qui ont quantity_str = NULL.
Run: python backfill_quantity.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select
from app.core.config import settings
from app.db.database import get_mongo_collection
from app.models.models import Product


async def backfill():
    engine = create_async_engine(settings.DATABASE_URL)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        result = await db.execute(
            select(Product.barcode, Product.name).where(Product.quantity_str.is_(None))
        )
        products = result.all()

    print(f"{len(products)} produits sans quantity_str à mettre à jour...")

    col = get_mongo_collection()
    updated = 0
    skipped = 0

    async with Session() as db:
        for barcode, name in products:
            doc = col.find_one(
                {"$or": [{"code": barcode}, {"_id": barcode}]},
                {"quantity": 1}
            )
            qty_str = (doc.get("quantity") or "").strip()[:50] if doc else ""
            if qty_str:
                await db.execute(
                    text("UPDATE products SET quantity_str = :q WHERE barcode = :b"),
                    {"q": qty_str, "b": barcode}
                )
                print(f"  ✓ {name[:40]:<40} -> {qty_str!r}")
                updated += 1
            else:
                print(f"  - {name[:40]:<40} -> (pas de quantity dans MongoDB)")
                skipped += 1

        await db.commit()

    print(f"\nDone. {updated} mis à jour, {skipped} sans donnée MongoDB.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill())

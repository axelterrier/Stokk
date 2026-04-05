from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.models.models import Product
from app.db.database import get_mongo_collection

def _build_image_url(barcode: str, doc: dict) -> str | None:
    """Construit l'URL image depuis images.selected.front quand image_front_url est absent."""
    try:
        front = doc.get("images", {}).get("selected", {}).get("front", {})
        # Préférer la langue française, sinon la première dispo
        lang_data = front.get("fr") or front.get("en") or next(iter(front.values()), None)
        if not lang_data:
            return None
        imgid = str(lang_data["imgid"])
        # Découpage du barcode en segments : 1234567890123 → 123/456/789/0123
        b = barcode.zfill(13)
        path = f"{b[0:3]}/{b[3:6]}/{b[6:9]}/{b[9:]}"
        return f"https://images.openfoodfacts.org/images/products/{path}/{imgid}.400.jpg"
    except Exception:
        return None


def _mongo_doc_to_product_dict(barcode: str, doc: dict) -> dict:
    nutriments = doc.get("nutriments", {})

    def _safe_float(val) -> float | None:
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    return {
        "barcode": barcode,
        "name": (
            doc.get("product_name_fr")
            or doc.get("product_name")
            or doc.get("product_name_en")
            or "Produit inconnu"
        ),
        "brand": (doc.get("brands") or "")[:500] or None,
        "category": (doc.get("categories") or "")[:1000] or None,
        "image_url": (doc.get("image_front_url") or doc.get("image_url") or _build_image_url(barcode, doc) or "")[:1000] or None,
        "nutriscore": (doc.get("nutriscore_grade") or "").upper()[:1] or None,
        "quantity_str": (doc.get("quantity") or "")[:50] or None,
        "energy_kcal": _safe_float(nutriments.get("energy-kcal_100g")),
        "proteins_g": _safe_float(nutriments.get("proteins_100g")),
        "carbs_g": _safe_float(nutriments.get("carbohydrates_100g")),
        "fat_g": _safe_float(nutriments.get("fat_100g")),
    }


async def lookup_product(barcode: str, db: AsyncSession) -> tuple[Product | None, str | None]:
    # 1. Cache PG
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    cached = result.scalar_one_or_none()
    if cached:
        return cached, "cache"

    # 2. MongoDB (Motor — vraiment async)
    col = get_mongo_collection()
    doc = await col.find_one({"$or": [{"code": barcode}, {"_id": barcode}]})
    if not doc:
        return None, None

    data = _mongo_doc_to_product_dict(barcode, doc)

    # INSERT ... ON CONFLICT DO NOTHING — safe en cas de double appel simultané
    stmt = pg_insert(Product).values(**data).on_conflict_do_nothing(index_elements=["barcode"])
    await db.execute(stmt)
    await db.commit()

    # Recharger depuis la BDD
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    product = result.scalar_one_or_none()
    return product, "openfoodfacts"
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update as sql_update, delete as sql_delete
from uuid import UUID

from app.db.database import get_db
from app.models.models import StockItem, ExpiryDate, User
from app.schemas.schemas import ScanResponse, StockItemCreate, StockItemOut, StockItemUpdate
from app.services.product_service import lookup_product
from app.core.security import get_current_user

router = APIRouter()


# ── GET /scan/{barcode} ───────────────────────────────────────────────────────

@router.get("/scan/{barcode}", response_model=ScanResponse)
async def scan_barcode(barcode: str, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """
    Lookup d'un code-barres : retourne les infos produit depuis le cache
    PostgreSQL ou le dump MongoDB OpenFoodFacts.
    """
    product, source = await lookup_product(barcode, db)
    if not product:
        return ScanResponse(found=False)
    return ScanResponse(found=True, source=source, product=product)


# ── POST /stock ───────────────────────────────────────────────────────────────

@router.post("/stock", response_model=StockItemOut, status_code=201)
async def add_stock_item(payload: StockItemCreate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload

    product, _ = await lookup_product(payload.product_barcode, db)
    if not product:
        raise HTTPException(status_code=404, detail="Produit introuvable — scannez d'abord le code-barres")

    item = StockItem(
        product_barcode=payload.product_barcode,
        quantity=payload.quantity,
        unit=payload.unit,
        location=payload.location,
        opened=payload.opened,
    )
    db.add(item)
    await db.flush()

    if payload.expiry_date:
        expiry = ExpiryDate(
            stock_item_id=item.id,
            expiry_date=payload.expiry_date,
            alert_days_before=payload.alert_days_before,
        )
        db.add(expiry)
        await db.flush()

    await db.commit()

    # Recharger avec les relations
    result = await db.execute(
        select(StockItem)
        .where(StockItem.id == item.id)
        .options(
            selectinload(StockItem.product),
            selectinload(StockItem.expiry_date),
        )
    )
    return result.scalar_one()


# ── GET /stock ────────────────────────────────────────────────────────────────

@router.get("/stock", response_model=list[StockItemOut])
async def list_stock(db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    """Liste tous les articles en stock."""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(StockItem)
        .options(
            selectinload(StockItem.product),
            selectinload(StockItem.expiry_date),
        )
        .order_by(StockItem.added_at.desc())
    )
    return result.scalars().all()


# ── PATCH /stock/{item_id} ────────────────────────────────────────────────────

@router.patch("/stock/{item_id}", response_model=StockItemOut)
async def update_stock_item(item_id: UUID, payload: StockItemUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    from sqlalchemy.orm import selectinload

    if not await db.get(StockItem, item_id):
        raise HTTPException(status_code=404, detail="Article introuvable")

    # Mise à jour des champs simples via UPDATE explicite
    fields = payload.model_fields_set
    update_values = {}
    if "quantity" in fields:
        update_values["quantity"] = payload.quantity
    if "unit" in fields:
        update_values["unit"] = payload.unit
    if "location" in fields:
        update_values["location"] = payload.location
    if "opened" in fields:
        update_values["opened"] = payload.opened

    if update_values:
        await db.execute(
            sql_update(StockItem).where(StockItem.id == item_id).values(**update_values)
        )

    # Gestion de la DLC
    if payload.clear_expiry:
        await db.execute(
            sql_delete(ExpiryDate).where(ExpiryDate.stock_item_id == item_id)
        )
    elif "expiry_date" in fields and payload.expiry_date is not None:
        existing = (await db.execute(
            select(ExpiryDate).where(ExpiryDate.stock_item_id == item_id)
        )).scalar_one_or_none()

        if existing:
            expiry_values = {"expiry_date": payload.expiry_date}
            if "alert_days_before" in fields:
                expiry_values["alert_days_before"] = payload.alert_days_before
            await db.execute(
                sql_update(ExpiryDate).where(ExpiryDate.stock_item_id == item_id).values(**expiry_values)
            )
        else:
            db.add(ExpiryDate(
                stock_item_id=item_id,
                expiry_date=payload.expiry_date,
                alert_days_before=payload.alert_days_before or 3,
            ))

    await db.commit()

    result = await db.execute(
        select(StockItem)
        .where(StockItem.id == item_id)
        .options(
            selectinload(StockItem.product),
            selectinload(StockItem.expiry_date),
        )
        .execution_options(populate_existing=True)
    )
    return result.scalar_one()


# ── DELETE /stock/{item_id} ───────────────────────────────────────────────────

@router.delete("/stock/{item_id}", status_code=204)
async def delete_stock_item(item_id: UUID, db: AsyncSession = Depends(get_db), _: User = Depends(get_current_user)):
    item = await db.get(StockItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Article introuvable")
    await db.delete(item)
    await db.commit()

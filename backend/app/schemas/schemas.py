from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel


# ── Product ───────────────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    barcode: str
    name: str
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None
    nutriscore: str | None = None
    energy_kcal: float | None = None
    proteins_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None

    model_config = {"from_attributes": True}


# ── Stock ─────────────────────────────────────────────────────────────────────

class ExpiryDateOut(BaseModel):
    id: UUID
    expiry_date: date
    alert_days_before: int
    alerted: bool

    model_config = {"from_attributes": True}


class StockItemCreate(BaseModel):
    product_barcode: str
    quantity: float
    unit: str = "unité"
    location: str | None = None
    opened: bool = False
    expiry_date: date | None = None
    alert_days_before: int = 3


class StockItemOut(BaseModel):
    id: UUID
    product_barcode: str
    quantity: float
    unit: str
    location: str | None
    opened: bool
    added_at: datetime
    product: ProductOut
    expiry_date: ExpiryDateOut | None = None

    model_config = {"from_attributes": True}


# ── Stock update ──────────────────────────────────────────────────────────────

class StockItemUpdate(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    location: str | None = None
    opened: bool | None = None
    expiry_date: date | None = None
    alert_days_before: int | None = None
    clear_expiry: bool = False


# ── Scan response ─────────────────────────────────────────────────────────────

class ScanResponse(BaseModel):
    found: bool
    source: str | None = None  # "cache" | "openfoodfacts" | None
    product: ProductOut | None = None

from __future__ import annotations
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel


# ── Location ───────────────────────────────────────────────────────────────────

class LocationOut(BaseModel):
    id: UUID
    name: str
    parent_id: UUID | None = None
    color: str | None = None
    model_config = {"from_attributes": True}


class LocationCreate(BaseModel):
    name: str
    parent_id: UUID | None = None
    color: str | None = None


class LocationUpdate(BaseModel):
    name: str | None = None
    parent_id: UUID | None = None
    color: str | None = None


# ── Product ───────────────────────────────────────────────────────────────────

class ProductOut(BaseModel):
    barcode: str
    name: str
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None
    nutriscore: str | None = None
    quantity_str: str | None = None
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
    location_id: UUID | None = None
    opened: bool = False
    expiry_date: date | None = None
    alert_days_before: int = 3


class StockItemOut(BaseModel):
    id: UUID
    product_barcode: str
    quantity: float
    unit: str
    location: LocationOut | None = None
    opened: bool
    added_at: datetime
    product: ProductOut
    expiry_date: ExpiryDateOut | None = None
    model_config = {"from_attributes": True}


# ── Stock update ──────────────────────────────────────────────────────────────

class StockItemUpdate(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    location_id: UUID | None = None
    opened: bool | None = None
    expiry_date: date | None = None
    alert_days_before: int | None = None
    clear_expiry: bool = False


# ── Users ─────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: UUID
    username: str
    email: str
    is_admin: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    password: str | None = None
    is_admin: bool | None = None


# ── Scan response ─────────────────────────────────────────────────────────────

class ScanResponse(BaseModel):
    found: bool
    source: str | None = None
    product: ProductOut | None = None


# ── Recipes ───────────────────────────────────────────────────────────────────

class RecipeIngredientCreate(BaseModel):
    product_barcode: str | None = None
    ingredient_name: str
    quantity: float
    unit: str = "unité"


class RecipeIngredientOut(BaseModel):
    id: UUID
    product_barcode: str | None = None
    ingredient_name: str
    quantity: float
    unit: str
    product: ProductOut | None = None
    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None
    ingredients: list[RecipeIngredientCreate] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    ingredients: list[RecipeIngredientCreate] | None = None


class RecipeOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    created_by: UUID
    created_at: datetime
    ingredients: list[RecipeIngredientOut] = []
    model_config = {"from_attributes": True}


class CookIngredientResult(BaseModel):
    ingredient_name: str
    requested: float
    unit: str
    available: float
    deducted: float
    status: str  # "ok" | "partial" | "not_in_stock" | "unlinked"


class CookResult(BaseModel):
    recipe_name: str
    results: list[CookIngredientResult]

"""
Shared fixtures — mock DB session and a helper to build a fake StockItem.
"""
import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient, ASGITransport

from main import app
from app.db.database import get_db


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_product(barcode: str = "3017620422003") -> MagicMock:
    p = MagicMock()
    p.barcode = barcode
    p.name = "Nutella"
    p.brand = "Ferrero"
    p.category = "Pâtes à tartiner"
    p.image_url = None
    p.nutriscore = "E"
    p.energy_kcal = 539.0
    p.proteins_g = 6.3
    p.carbs_g = 57.5
    p.fat_g = 30.9
    p.created_at = datetime.utcnow()
    p.updated_at = datetime.utcnow()
    return p


def make_stock_item(item_id: uuid.UUID | None = None, barcode: str = "3017620422003") -> MagicMock:
    item = MagicMock()
    item.id = item_id or uuid.uuid4()
    item.product_barcode = barcode
    item.quantity = 1.0
    item.unit = "unité"
    item.location = "Placard"
    item.opened = False
    item.added_at = datetime.utcnow()
    item.product = make_product(barcode)
    item.expiry_date = None
    return item


# ── DB mock factory ───────────────────────────────────────────────────────────

def make_db_session() -> AsyncMock:
    """Returns a mock AsyncSession with the minimal interface used by routes."""
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    return session


# ── App-level fixture with overridable DB ─────────────────────────────────────

@pytest.fixture
def db_mock():
    return make_db_session()


@pytest.fixture
async def client(db_mock):
    async def override_get_db():
        yield db_mock

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

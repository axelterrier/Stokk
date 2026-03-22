"""
Tests des routes HTTP — DB et MongoDB mockés.
Vérifie le comportement post-refactoring (plus de household_id).
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from tests.conftest import make_product, make_stock_item


# ── /health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── GET /api/v1/scan/{barcode} ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scan_found(client):
    product = make_product()
    with patch("app.routes.stock.lookup_product", new=AsyncMock(return_value=(product, "cache"))):
        r = await client.get("/api/v1/scan/3017620422003")
    assert r.status_code == 200
    data = r.json()
    assert data["found"] is True
    assert data["source"] == "cache"
    assert data["product"]["barcode"] == "3017620422003"
    assert data["product"]["name"] == "Nutella"


@pytest.mark.asyncio
async def test_scan_not_found(client):
    with patch("app.routes.stock.lookup_product", new=AsyncMock(return_value=(None, None))):
        r = await client.get("/api/v1/scan/0000000000000")
    assert r.status_code == 200
    assert r.json()["found"] is False


# ── GET /api/v1/stock ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_stock_no_household_id_required(client, db_mock):
    """GET /stock ne doit plus exiger household_id."""
    items = [make_stock_item(), make_stock_item()]

    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = items
    db_mock.execute = AsyncMock(return_value=execute_result)

    r = await client.get("/api/v1/stock")
    assert r.status_code == 200
    assert len(r.json()) == 2


@pytest.mark.asyncio
async def test_list_stock_empty(client, db_mock):
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    db_mock.execute = AsyncMock(return_value=execute_result)

    r = await client.get("/api/v1/stock")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_list_stock_ignores_household_id_param(client, db_mock):
    """Un ancien client passant household_id ne doit pas planter (paramètre ignoré)."""
    execute_result = MagicMock()
    execute_result.scalars.return_value.all.return_value = []
    db_mock.execute = AsyncMock(return_value=execute_result)

    r = await client.get("/api/v1/stock?household_id=00000000-0000-0000-0000-000000000001")
    assert r.status_code == 200


# ── POST /api/v1/stock ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_stock_no_household_id(client, db_mock):
    """POST /stock ne doit plus exiger household_id dans le body."""
    item = make_stock_item()
    product = make_product()

    execute_result = MagicMock()
    execute_result.scalar_one.return_value = item
    db_mock.execute = AsyncMock(return_value=execute_result)

    with patch("app.routes.stock.lookup_product", new=AsyncMock(return_value=(product, "cache"))):
        r = await client.post("/api/v1/stock", json={
            "product_barcode": "3017620422003",
            "quantity": 2.0,
            "unit": "unité",
        })

    assert r.status_code == 201


@pytest.mark.asyncio
async def test_add_stock_product_not_found(client):
    with patch("app.routes.stock.lookup_product", new=AsyncMock(return_value=(None, None))):
        r = await client.post("/api/v1/stock", json={
            "product_barcode": "9999999999999",
            "quantity": 1.0,
            "unit": "unité",
        })
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_add_stock_rejects_household_id_no_longer_needed(client, db_mock):
    """Un body avec household_id doit être accepté sans erreur (champ ignoré par Pydantic)."""
    item = make_stock_item()
    product = make_product()

    execute_result = MagicMock()
    execute_result.scalar_one.return_value = item
    db_mock.execute = AsyncMock(return_value=execute_result)

    with patch("app.routes.stock.lookup_product", new=AsyncMock(return_value=(product, "cache"))):
        r = await client.post("/api/v1/stock", json={
            "household_id": "00000000-0000-0000-0000-000000000001",  # champ fantôme
            "product_barcode": "3017620422003",
            "quantity": 1.0,
            "unit": "unité",
        })
    # Pydantic ignore les champs inconnus par défaut → doit passer
    assert r.status_code == 201


# ── DELETE /api/v1/stock/{item_id} ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_stock_returns_204(client, db_mock):
    item_id = uuid.uuid4()
    item = make_stock_item(item_id=item_id)
    db_mock.get = AsyncMock(return_value=item)

    r = await client.delete(f"/api/v1/stock/{item_id}")
    assert r.status_code == 204
    assert r.content == b""


@pytest.mark.asyncio
async def test_delete_stock_not_found(client, db_mock):
    db_mock.get = AsyncMock(return_value=None)
    r = await client.delete(f"/api/v1/stock/{uuid.uuid4()}")
    assert r.status_code == 404


# ── PATCH /api/v1/stock/{item_id} ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_stock(client, db_mock):
    item_id = uuid.uuid4()
    item = make_stock_item(item_id=item_id)

    db_mock.get = AsyncMock(return_value=item)
    execute_result = MagicMock()
    execute_result.scalar_one.return_value = item
    db_mock.execute = AsyncMock(return_value=execute_result)

    r = await client.patch(f"/api/v1/stock/{item_id}", json={"quantity": 5.0})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_update_stock_not_found(client, db_mock):
    db_mock.get = AsyncMock(return_value=None)
    r = await client.patch(f"/api/v1/stock/{uuid.uuid4()}", json={"quantity": 1.0})
    assert r.status_code == 404

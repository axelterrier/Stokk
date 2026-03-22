"""
Pure Pydantic schema validation — no DB, no HTTP.
Vérifie que les schémas post-refactoring ne contiennent plus household_id.
"""
import uuid
from datetime import date
import pytest
from pydantic import ValidationError

from app.schemas.schemas import StockItemCreate, StockItemUpdate, ScanResponse


class TestStockItemCreate:
    def test_minimal_valid(self):
        payload = StockItemCreate(product_barcode="3017620422003", quantity=2.0, unit="unité")
        assert payload.product_barcode == "3017620422003"
        assert payload.quantity == 2.0
        assert payload.unit == "unité"

    def test_defaults(self):
        payload = StockItemCreate(product_barcode="abc", quantity=1, unit="g")
        assert payload.opened is False
        assert payload.expiry_date is None
        assert payload.alert_days_before == 3
        assert payload.location is None

    def test_no_household_id_field(self):
        """household_id doit avoir été retiré du schéma."""
        assert not hasattr(StockItemCreate.model_fields, "household_id"), \
            "household_id ne doit plus exister dans StockItemCreate"
        assert "household_id" not in StockItemCreate.model_fields

    def test_with_expiry(self):
        payload = StockItemCreate(
            product_barcode="123",
            quantity=1,
            unit="L",
            expiry_date=date(2026, 12, 31),
            alert_days_before=7,
        )
        assert payload.expiry_date == date(2026, 12, 31)
        assert payload.alert_days_before == 7

    def test_rejects_extra_unknown_field(self):
        """Un payload avec household_id doit être ignoré (extra='ignore' par défaut)
        ou déclencher une erreur selon la config du modèle."""
        # On vérifie juste que le champ n'est pas dans model_fields
        assert "household_id" not in StockItemCreate.model_fields


class TestStockItemUpdate:
    def test_all_optional(self):
        # Aucun champ obligatoire
        payload = StockItemUpdate()
        assert payload.quantity is None
        assert payload.clear_expiry is False

    def test_partial_update(self):
        payload = StockItemUpdate(quantity=3.5, location="Frigo")
        assert payload.quantity == 3.5
        assert payload.location == "Frigo"
        assert payload.unit is None


class TestScanResponse:
    def test_not_found(self):
        r = ScanResponse(found=False)
        assert r.found is False
        assert r.product is None
        assert r.source is None

    def test_found(self):
        from app.schemas.schemas import ProductOut
        product = ProductOut(barcode="123", name="Test")
        r = ScanResponse(found=True, source="cache", product=product)
        assert r.found is True
        assert r.source == "cache"
        assert r.product.barcode == "123"

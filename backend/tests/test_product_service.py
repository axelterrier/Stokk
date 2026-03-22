"""
Tests de la fonction pure _mongo_doc_to_product_dict — aucune DB ni réseau requis.
"""
from app.services.product_service import _mongo_doc_to_product_dict


BARCODE = "3017620422003"


class TestMongoDocToProductDict:
    def test_french_name_preferred(self):
        doc = {"product_name_fr": "Nutella FR", "product_name": "Nutella EN"}
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["name"] == "Nutella FR"

    def test_falls_back_to_english_name(self):
        doc = {"product_name": "Nutella EN"}
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["name"] == "Nutella EN"

    def test_unknown_product_fallback(self):
        result = _mongo_doc_to_product_dict(BARCODE, {})
        assert result["name"] == "Produit inconnu"

    def test_barcode_set_correctly(self):
        result = _mongo_doc_to_product_dict(BARCODE, {"product_name": "X"})
        assert result["barcode"] == BARCODE

    def test_nutriscore_uppercased(self):
        doc = {"product_name": "X", "nutriscore_grade": "b"}
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["nutriscore"] == "B"

    def test_nutriscore_none_when_missing(self):
        result = _mongo_doc_to_product_dict(BARCODE, {"product_name": "X"})
        assert result["nutriscore"] is None

    def test_nutriments_parsed(self):
        doc = {
            "product_name": "X",
            "nutriments": {
                "energy-kcal_100g": "539",
                "proteins_100g": "6.3",
                "carbohydrates_100g": "57.5",
                "fat_100g": "30.9",
            },
        }
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["energy_kcal"] == 539.0
        assert result["proteins_g"] == 6.3
        assert result["carbs_g"] == 57.5
        assert result["fat_g"] == 30.9

    def test_invalid_nutriment_returns_none(self):
        doc = {"product_name": "X", "nutriments": {"energy-kcal_100g": "n/a"}}
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["energy_kcal"] is None

    def test_image_url_fallback(self):
        doc = {"product_name": "X", "image_url": "http://example.com/img.jpg"}
        result = _mongo_doc_to_product_dict(BARCODE, doc)
        assert result["image_url"] == "http://example.com/img.jpg"

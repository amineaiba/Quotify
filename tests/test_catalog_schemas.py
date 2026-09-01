import pytest
from pydantic import ValidationError

from app.schemas.catalog import CatalogItemWrite


def test_write_rejects_empty_tiers():
    with pytest.raises(ValidationError):
        CatalogItemWrite(name="Flyer", unit="flyer", tiers=[])


def test_write_rejects_duplicate_min_qty():
    with pytest.raises(ValidationError):
        CatalogItemWrite(
            name="Flyer",
            unit="flyer",
            tiers=[
                {"min_qty": 100, "unit_price": 10},
                {"min_qty": 100, "unit_price": 8},
            ],
        )


def test_write_accepts_valid_payload():
    item = CatalogItemWrite(
        name="Flyer",
        unit="flyer",
        tiers=[{"min_qty": 100, "unit_price": 10}, {"min_qty": 500, "unit_price": 8}],
    )
    assert item.tiers[0].min_qty == 100

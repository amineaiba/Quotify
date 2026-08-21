import json
from pathlib import Path

CATALOG = json.loads((Path("data") / "catalog.json").read_text(encoding="utf-8"))
MESSAGES = json.loads((Path("evals") / "datasets" / "messages.json").read_text(encoding="utf-8"))

CATALOG_IDS = {item["id"] for item in CATALOG}


def test_every_gold_id_exists_in_catalog():
    bad = [
        m["text"][:40]
        for m in MESSAGES
        if m["gold"] is not None and m["gold"] not in CATALOG_IDS
    ]
    assert not bad, f"gold id not in catalog: {bad}"


def test_tiers_min_qty_ascending():
    for item in CATALOG:
        qtys = [t["min_qty"] for t in item["tiers"]]
        assert qtys == sorted(qtys), f"{item['name']}: tiers not ordered by min_qty"


def test_tiers_unit_price_descending():
    """Bigger order, cheaper unit — true of every item in the source data."""
    for item in CATALOG:
        prices = [t["unit_price"] for t in item["tiers"]]
        assert prices == sorted(prices, reverse=True), f"{item['name']}: price rises with qty"

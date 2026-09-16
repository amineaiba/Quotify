import json
from pathlib import Path

from evals.multi_item_eval import CATALOG

DATASET_PATH = Path("evals") / "datasets" / "multi_item.json"
CASES = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

CATALOG_NAMES = {item["name"] for item in CATALOG}


def test_every_case_has_text_and_expected_items():
    for case in CASES:
        assert isinstance(case["text"], str) and case["text"]
        assert isinstance(case["expected_items"], list) and case["expected_items"]


def test_every_expected_item_exists_in_eval_catalog():
    bad = [
        (case["text"][:40], name)
        for case in CASES
        for name in case["expected_items"]
        if name not in CATALOG_NAMES
    ]
    assert not bad, f"expected item not in eval catalog: {bad}"


def test_dataset_has_a_multi_item_and_a_partial_info_case():
    counts = [len(case["expected_items"]) for case in CASES]
    assert max(counts) > 1, "no case expects more than one item"
    assert min(counts) == 1, "no partial-info case (exactly one priceable item)"

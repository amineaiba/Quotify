import json
from pathlib import Path

DATASET_PATH = Path("evals") / "datasets" / "confirmations.json"
CASES = json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def test_every_case_has_text_and_expected_flag():
    for case in CASES:
        assert isinstance(case["confirm_text"], str) and case["confirm_text"]
        assert isinstance(case["should_confirm"], bool)


def test_dataset_has_both_positive_and_negative_cases():
    flags = {case["should_confirm"] for case in CASES}
    assert flags == {True, False}

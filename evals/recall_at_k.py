# Run:  docker compose exec api python evals/recall_at_k.py --business-id <uuid> [-v]
# Or set CATALOG_EVAL_BUSINESS_ID instead of passing --business-id each time.
#
# business_id is required: /api/v1/catalog/search has no auth (dev/testing
# only), so the caller says up front which business's catalog to search —
# use the id of whichever business owns your seeded dev catalog.

import argparse
import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).parent / "datasets" / "messages.json"
API_URL = "http://localhost:8000/api/v1/catalog/search"

MESSAGES = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
SCORABLE = [m for m in MESSAGES if m["gold"] is not None]  # gold=None has no answer to score


def retrieve(message: str, k: int, business_id: str) -> list[int]:
    response = httpx.post(
        API_URL, json={"message": message, "k": k, "business_id": business_id}, timeout=30
    )
    response.raise_for_status()
    return [row["id"] for row in response.json()]


def recall_at_k(k: int, business_id: str) -> float:
    hits = 0
    for m in SCORABLE:
        top = retrieve(m["text"], k, business_id)
        hit = m["gold"] in top
        hits += 1 if hit else 0
        mark = "HIT " if hit else "MISS"
        logger.debug("%s wanted %2d, got %s   %s", mark, m["gold"], top, m["text"][:52])
    score = hits / len(SCORABLE)
    logger.info("recall@%d = %.2f   (%d/%d)", k, score, hits, len(SCORABLE))
    return score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", help="show per-message hit/miss")
    parser.add_argument(
        "--business-id",
        default=os.environ.get("CATALOG_EVAL_BUSINESS_ID"),
        help="business whose catalog to search (or set CATALOG_EVAL_BUSINESS_ID)",
    )
    args = parser.parse_args()
    if not args.business_id:
        parser.error("--business-id is required (or set CATALOG_EVAL_BUSINESS_ID)")

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    for k in (1, 3):
        recall_at_k(k, args.business_id)

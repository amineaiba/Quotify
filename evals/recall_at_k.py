# Run:  python evals/recall_at_k.py --token <access token> [-v]
# Or set CATALOG_EVAL_TOKEN instead of passing --token each time.
#
# /api/v1/catalog/search needs login: log in as the business that owns your
# dev catalog (POST /api/v1/auth/jwt/login) and pass the access token.

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


def retrieve(message: str, k: int, token: str) -> list[int]:
    response = httpx.post(
        API_URL,
        json={"message": message, "k": k},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    response.raise_for_status()
    return [row["id"] for row in response.json()]


def recall_at_k(k: int, token: str) -> float:
    hits = 0
    for m in SCORABLE:
        top = retrieve(m["text"], k, token)
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
        "--token",
        default=os.environ.get("CATALOG_EVAL_TOKEN"),
        help="access token of the business to search (or set CATALOG_EVAL_TOKEN)",
    )
    args = parser.parse_args()
    if not args.token:
        parser.error("--token is required (or set CATALOG_EVAL_TOKEN)")

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    for k in (1, 3):
        recall_at_k(k, args.token)

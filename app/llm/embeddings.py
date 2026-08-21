import numpy as np
from google.genai import types

from app.core.config import get_settings
from app.llm.client import get_client

# Must match the vector column width in app/models/catalog.py and the
# Alembic migration. Change all three together, or searches break silently.
EMBED_DIM = 3072


def embed(texts: list[str], task_type: str) -> list[list[float]]:
    """task_type: RETRIEVAL_DOCUMENT for catalog text, RETRIEVAL_QUERY for a
    client message. Same text embeds differently depending on which."""
    response = get_client().models.embed_content(
        model=get_settings().embed_model,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    vectors = np.array([e.values for e in response.embeddings])
    normalised = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    return normalised.tolist()

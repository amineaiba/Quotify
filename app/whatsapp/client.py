import asyncio
import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"
SEND_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.0


def _is_retryable(err: httpx.HTTPError) -> bool:
    """Network errors, rate limits and Meta server errors may pass on a retry. A 4xx will not."""
    if isinstance(err, httpx.HTTPStatusError):
        status = err.response.status_code
        return status == 429 or status >= 500
    return isinstance(err, httpx.TransportError)


async def send_message(phone_number_id: str, to: str, text: str) -> None:
    """Sends a text reply back to a client via the WhatsApp Cloud API.

    Retries a few times on temporary errors, then raises the last one.
    """
    settings = get_settings()
    url = f"{GRAPH_API_BASE}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

    for attempt in range(1, SEND_ATTEMPTS + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return
        except httpx.HTTPError as err:
            if attempt == SEND_ATTEMPTS or not _is_retryable(err):
                raise
            logger.warning("whatsapp send failed (attempt %d/%d): %r", attempt, SEND_ATTEMPTS, err)
            await asyncio.sleep(RETRY_DELAY_SECONDS * attempt)

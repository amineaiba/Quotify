import httpx

from app.core.config import get_settings

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


async def send_message(phone_number_id: str, to: str, text: str) -> None:
    """Sends a text reply back to a client via the WhatsApp Cloud API."""
    settings = get_settings()
    url = f"{GRAPH_API_BASE}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
    response.raise_for_status()

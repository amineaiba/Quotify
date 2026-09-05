import httpx
import pytest

from app.whatsapp import client as whatsapp_client


def _patch_transport(monkeypatch, handler):
    """Redirects the module's AsyncClient onto a mock transport instead of the network."""
    original_init = httpx.AsyncClient.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "__init__", patched_init)


async def test_send_message_posts_expected_request(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        captured["body"] = request.content
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    _patch_transport(monkeypatch, handler)

    await whatsapp_client.send_message("123456", "+213555000000", "9500 DA")

    assert captured["url"] == "https://graph.facebook.com/v21.0/123456/messages"
    assert captured["headers"]["authorization"].startswith("Bearer ")
    assert b'"to":"+213555000000"' in captured["body"]
    assert b'"body":"9500 DA"' in captured["body"]


async def test_send_message_raises_on_error_response(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "bad token"})

    _patch_transport(monkeypatch, handler)

    with pytest.raises(httpx.HTTPStatusError):
        await whatsapp_client.send_message("123456", "+213555000000", "hi")

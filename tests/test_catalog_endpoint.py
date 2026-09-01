from app.llm.embeddings import EMBED_DIM
from tests.conftest import register_and_login

FAKE_VECTOR = [0.1] * EMBED_DIM


def fake_embed(texts: list[str], task_type: str) -> list[list[float]]:
    return [FAKE_VECTOR for _ in texts]


async def _auth_headers(client, email="owner@atelier.dz") -> dict:
    token = await register_and_login(client, email)
    return {"Authorization": f"Bearer {token}"}


async def test_create_item_requires_auth(client, session):
    response = await client.post(
        "/api/v1/catalog/items",
        json={"name": "Flyer", "unit": "flyer", "tiers": [{"min_qty": 1, "unit_price": 1}]},
    )
    assert response.status_code == 401


async def test_create_and_get_item(client, session, monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)
    headers = await _auth_headers(client)

    create = await client.post(
        "/api/v1/catalog/items",
        json={"name": "Flyer", "unit": "flyer", "tiers": [{"min_qty": 100, "unit_price": 10}]},
        headers=headers,
    )
    assert create.status_code == 201
    item_id = create.json()["id"]

    get_response = await client.get(f"/api/v1/catalog/items/{item_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Flyer"
    assert get_response.json()["tiers"][0]["min_qty"] == 100


async def test_list_items_scoped_to_caller(client, session, monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)
    headers_a = await _auth_headers(client, "a@atelier.dz")
    headers_b = await _auth_headers(client, "b@atelier.dz")
    await client.post(
        "/api/v1/catalog/items",
        json={"name": "A item", "unit": "u", "tiers": [{"min_qty": 1, "unit_price": 1}]},
        headers=headers_a,
    )

    response = await client.get("/api/v1/catalog/items", headers=headers_b)

    assert response.status_code == 200
    assert response.json() == []


async def test_get_item_from_another_business_returns_404(client, session, monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)
    headers_a = await _auth_headers(client, "a2@atelier.dz")
    headers_b = await _auth_headers(client, "b2@atelier.dz")
    create = await client.post(
        "/api/v1/catalog/items",
        json={"name": "A item", "unit": "u", "tiers": [{"min_qty": 1, "unit_price": 1}]},
        headers=headers_a,
    )
    item_id = create.json()["id"]

    response = await client.get(f"/api/v1/catalog/items/{item_id}", headers=headers_b)

    assert response.status_code == 404


async def test_update_item(client, session, monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)
    headers = await _auth_headers(client, "u@atelier.dz")
    create = await client.post(
        "/api/v1/catalog/items",
        json={"name": "Flyer", "unit": "flyer", "tiers": [{"min_qty": 100, "unit_price": 10}]},
        headers=headers,
    )
    item_id = create.json()["id"]

    response = await client.put(
        f"/api/v1/catalog/items/{item_id}",
        json={"name": "Flyer", "unit": "flyer", "tiers": [{"min_qty": 100, "unit_price": 20}]},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["tiers"][0]["unit_price"] == 20


async def test_delete_item(client, session, monkeypatch):
    monkeypatch.setattr("app.services.catalog.embed", fake_embed)
    headers = await _auth_headers(client, "d@atelier.dz")
    create = await client.post(
        "/api/v1/catalog/items",
        json={"name": "Flyer", "unit": "flyer", "tiers": [{"min_qty": 100, "unit_price": 10}]},
        headers=headers,
    )
    item_id = create.json()["id"]

    delete_response = await client.delete(f"/api/v1/catalog/items/{item_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/catalog/items/{item_id}", headers=headers)
    assert get_response.status_code == 404


async def test_delete_unknown_item_returns_404(client, session):
    headers = await _auth_headers(client, "e@atelier.dz")
    response = await client.delete(
        "/api/v1/catalog/items/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404

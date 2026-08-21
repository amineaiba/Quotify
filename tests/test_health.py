from httpx import AsyncClient


async def test_health_reports_db_ok(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "ok"}

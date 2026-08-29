async def test_register_creates_business(client, session):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "owner@atelier.dz", "password": "s3cret-pw", "name": "Atelier Print"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "owner@atelier.dz"
    assert body["name"] == "Atelier Print"
    assert "password" not in body
    assert "hashed_password" not in body
    assert "api_key" not in body  # never exposed by the auth schemas


async def test_register_duplicate_email_rejected(client, session):
    payload = {"email": "dup@atelier.dz", "password": "s3cret-pw", "name": "A"}
    await client.post("/api/v1/auth/register", json=payload)

    response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 400


async def test_login_returns_jwt_token(client, session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@atelier.dz", "password": "s3cret-pw", "name": "A"},
    )

    response = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "login@atelier.dz", "password": "s3cret-pw"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_users_me_requires_auth(client, session):
    response = await client.get("/api/v1/auth/users/me")

    assert response.status_code == 401


async def test_users_me_returns_business(client, session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "me@atelier.dz", "password": "s3cret-pw", "name": "Atelier Print"},
    )
    login = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "me@atelier.dz", "password": "s3cret-pw"},
    )
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/users/me", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me@atelier.dz"

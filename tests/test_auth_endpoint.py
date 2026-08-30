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
    assert body["refresh_token"]


async def test_refresh_rotates_tokens(client, session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@atelier.dz", "password": "s3cret-pw", "name": "A"},
    )
    login = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "refresh@atelier.dz", "password": "s3cret-pw"},
    )
    old_refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/jwt/refresh", json={"refresh_token": old_refresh_token}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"] != old_refresh_token

    reuse = await client.post(
        "/api/v1/auth/jwt/refresh", json={"refresh_token": old_refresh_token}
    )
    assert reuse.status_code == 401  # rotation: old token is now revoked


async def test_refresh_rejects_unknown_token(client, session):
    response = await client.post(
        "/api/v1/auth/jwt/refresh", json={"refresh_token": "not-a-real-token"}
    )

    assert response.status_code == 401


async def test_logout_revokes_refresh_token(client, session):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@atelier.dz", "password": "s3cret-pw", "name": "A"},
    )
    login = await client.post(
        "/api/v1/auth/jwt/login",
        data={"username": "logout@atelier.dz", "password": "s3cret-pw"},
    )
    refresh_token = login.json()["refresh_token"]

    logout_response = await client.post(
        "/api/v1/auth/jwt/logout", json={"refresh_token": refresh_token}
    )
    assert logout_response.status_code == 204

    reuse = await client.post(
        "/api/v1/auth/jwt/refresh", json={"refresh_token": refresh_token}
    )
    assert reuse.status_code == 401


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

def test_me_missing_jwt_returns_401(client) -> None:
    response = client.get("/v1/me")
    assert response.status_code == 401

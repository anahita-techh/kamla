def test_me_upserts_user(client, engine) -> None:
    response = client.get("/v1/me", headers={"Authorization": "Bearer user-a"})
    assert response.status_code == 200
    body = response.json()
    assert body["clerk_user_id"] == "clerk_user_a"
    assert body["email"] == "a@example.com"
    assert body["onboarding_completed"] is False
    assert body["timezone"] is None

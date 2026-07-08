def create_user(client, username="alice", max_requests=2, bucket_capacity=2):
    response = client.post(
        "/users",
        json={
            "username": username,
            "plan": "pro",
            "rate_limit": {
                "algorithm": "token_bucket",
                "max_requests": max_requests,
                "time_window": 60,
                "refill_rate": 0,
                "bucket_capacity": bucket_capacity,
            },
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "ok"


def test_create_user_returns_api_key(client):
    user = create_user(client)

    assert user["username"] == "alice"
    assert user["api_key"]
    assert user["rate_limits"][0]["algorithm"] == "token_bucket"


def test_protected_endpoint_requires_valid_api_key(client):
    missing_key = client.get("/protected")
    invalid_key = client.get("/protected", headers={"X-API-Key": "bad-key"})

    assert missing_key.status_code == 401
    assert invalid_key.status_code == 401


def test_protected_endpoint_allows_valid_user(client):
    user = create_user(client)

    response = client.get("/protected", headers={"X-API-Key": user["api_key"]})

    assert response.status_code == 200
    assert response.get_json()["data"]["message"] == "Request allowed."


def test_rate_limit_exceeded_returns_429(client):
    user = create_user(client, max_requests=2, bucket_capacity=2)
    headers = {"X-API-Key": user["api_key"]}

    assert client.get("/protected", headers=headers).status_code == 200
    assert client.get("/protected", headers=headers).status_code == 200
    blocked = client.get("/protected", headers=headers)

    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert blocked.get_json()["error"]["type"] == "rate_limit_exceeded"


def test_logs_and_stats_are_recorded(client):
    user = create_user(client)
    headers = {"X-API-Key": user["api_key"]}

    client.get("/protected", headers=headers)
    logs = client.get("/logs")
    stats = client.get("/stats")

    assert logs.status_code == 200
    assert len(logs.get_json()["data"]) >= 1
    assert stats.get_json()["data"]["total_requests"] >= 1

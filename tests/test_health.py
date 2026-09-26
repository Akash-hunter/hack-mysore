from talent_platform import create_app


def test_index_renders_discovery_frontend():
    client = create_app({"TESTING": True}).test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert "Recruiter dashboard" in response.get_data(as_text=True)
    assert "Maya Chen" in response.get_data(as_text=True)
    assert "Northbridge Institute" in response.get_data(as_text=True)


def test_health_returns_ok():
    client = create_app({"TESTING": True}).test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}

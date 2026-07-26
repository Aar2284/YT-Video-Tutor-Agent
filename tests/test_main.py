import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthEndpoints:
    def test_register_missing_fields(self, client):
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422  # Validation error

    def test_login_missing_fields(self, client):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422

    def test_register_username_too_short(self, client):
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "password": "validpass"
        })
        assert response.status_code == 400

    def test_register_password_too_short(self, client):
        response = client.post("/api/auth/register", json={
            "username": "testuser",
            "password": "12345"
        })
        assert response.status_code == 400


class TestVideoEndpoints:
    def test_add_video_no_auth(self, client):
        response = client.post("/api/videos", json={"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"})
        assert response.status_code == 401

    def test_list_videos_no_auth(self, client):
        response = client.get("/api/videos")
        assert response.status_code == 401

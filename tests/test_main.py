from fastapi.testclient import TestClient


def test_app(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200

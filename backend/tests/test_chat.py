from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_chat_demo_mode():
    response = client.post("/chat", json={"query": "How long does shipping take?"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "verified" in data

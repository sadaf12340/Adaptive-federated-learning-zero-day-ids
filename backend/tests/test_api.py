from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_and_demo_workflow():
    health = client.get("/api/health")
    assert health.status_code == 200
    generated = client.post("/api/demo/generate?rows=300&seed=5")
    assert generated.status_code == 200
    assert generated.json()["rows"] == 300

    trained = client.post("/api/federated/train", json={"clients":3,"rounds":2,"epochs":1,"learning_rate":0.01,"drift_sensitivity":0.15,"adaptive":True})
    assert trained.status_code == 200
    assert len(trained.json()["rounds"]) == 2

def test_settings_persist():
    response = client.put("/api/settings", json={"settings":{"clients":4,"theme":"dark"}})
    assert response.status_code == 200
    assert client.get("/api/settings").json()["clients"] == 4

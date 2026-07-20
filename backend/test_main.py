import os
# Inject in-memory SQLite for testing before importing anything that connects to DB
os.environ["DB_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from main import app, get_redis

class MockRedis:
    def lpush(self, name, *values):
        pass
    def ping(self):
        return True

def override_get_redis():
    return MockRedis()

app.dependency_overrides[get_redis] = override_get_redis

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200

def test_create_and_list_tasks():
    # Create task
    response = client.post("/tasks", json={"payload": "test payload"})
    assert response.status_code == 200
    task_id = response.json()["id"]
    
    # List tasks
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    assert tasks[0]["payload"] == "test payload"
    assert tasks[0]["status"] == "pending"

def test_get_task():
    response = client.post("/tasks", json={"payload": "test single"})
    task_id = response.json()["id"]
    
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["payload"] == "test single"

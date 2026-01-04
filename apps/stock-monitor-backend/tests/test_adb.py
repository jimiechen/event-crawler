import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_adb_health():
    response = client.post("/health", json={
        "status": "healthy",
        "adb_available": True,
        "devices": [
            {
                "device_id": "test_device_1",
                "connected": True,
                "serial": "test_serial",
                "model": "TestPhone"
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["code"] == 0

def test_adb_app_list():
    response = client.post("/app_list", json={
        "device_id": "test_device_1",
        "apps": [
            {
                "package_name": "com.test.app",
                "is_system": False,
                "enabled": True
            }
        ]
    })
    assert response.status_code == 200
    assert response.json()["received_count"] == 1

def test_adb_events():
    response = client.post("/events", json={
        "type": "event",
        "device_id": "test_device_1",
        "action": "click",
        "data": {
            "success": True,
            "result": "Clicked"
        },
        "timestamp": "2026-01-04T12:00:00.000Z"
    })
    assert response.status_code == 200

def test_adb_command_send():
    response = client.post("/command/send", json={
        "device_id": "test_device_1",
        "action": "home"
    })
    assert response.status_code == 200

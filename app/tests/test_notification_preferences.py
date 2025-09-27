import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def user_token():
    # Replace with logic to get a valid token for a test user
    return "test-token"

def test_create_notification_preferences(user_token):
    payload = {
        "preferred_method": "email",
        "phone_number": "1234567890",
        "email": "test@example.com"
    }
    response = client.post(
        "/notifications/preferences",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["preferred_method"] == "email"
    assert data["phone_number"] == "1234567890"
    assert data["email"] == "test@example.com"

def test_get_notification_preferences(user_token):
    response = client.get(
        "/notifications/preferences",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "preferred_method" in data

def test_update_notification_preferences(user_token):
    payload = {
        "preferred_method": "sms",
        "phone_number": "9876543210"
    }
    response = client.put(
        "/notifications/preferences",
        json=payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["preferred_method"] == "sms"
    assert data["phone_number"] == "9876543210"

def test_delete_notification_preferences(user_token):
    response = client.delete(
        "/notifications/preferences",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Notification preferences deleted successfully"

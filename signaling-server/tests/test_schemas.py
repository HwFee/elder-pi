from datetime import datetime

from app.schemas import UserCreate, ContactResponse


def test_user_create_validates_email():
    data = UserCreate(email="alice@example.com", password="secret", full_name="Alice")
    assert data.email == "alice@example.com"


def test_contact_response_serializes():
    class FakeContact:
        id = "c1"
        device_id = "d1"
        user_id = "u1"
        display_name = "Alice"
        button_index = 1
        avatar_path = None
        created_at = datetime.utcnow()

    response = ContactResponse.model_validate(FakeContact())
    assert response.display_name == "Alice"

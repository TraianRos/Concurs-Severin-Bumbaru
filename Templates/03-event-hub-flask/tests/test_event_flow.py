from app import create_app
from app.models.entities import Event


def create_test_app():
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )


def test_create_event_and_register_attendee():
    app = create_test_app()
    client = app.test_client()

    response = client.post(
        "/events/new",
        data={
            "title": "Test Driven Demo",
            "location": "Lab 9",
            "start_date": "2026-05-01 09:00",
            "seats": "10",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200

    with app.app_context():
        event = Event.query.filter_by(title="Test Driven Demo").first()
        assert event is not None

    register_response = client.post(
        f"/events/{event.id}/register",
        data={"full_name": "Elena Demo", "email": "elena@example.com"},
        follow_redirects=True,
    )
    assert register_response.status_code == 200
    assert b"Registration completed." in register_response.data


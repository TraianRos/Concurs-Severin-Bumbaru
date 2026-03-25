from app import create_app
from app.extensions import db
from app.models import Category, Department, Incident, Notification, User


def create_test_app():
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )


def seed_reference_data():
    department = Department(
        name="Serviciul Drumuri",
        description="Probleme de carosabil.",
        contact_email="drumuri@test.local",
    )
    db.session.add(department)
    db.session.flush()

    category = Category(
        name="Groapa",
        description="Groapa in asfalt.",
        default_department_id=department.id,
    )
    db.session.add(category)

    operator = User(
        full_name="Operator Test",
        email="operator@test.local",
        role="operator",
        department_id=department.id,
    )
    operator.set_password("operator123")
    db.session.add(operator)
    db.session.commit()

    return department.id, category.id


def test_citizen_can_create_incident_and_receive_notification_after_operator_update():
    app = create_test_app()

    with app.app_context():
        department_id, category_id = seed_reference_data()

    client = app.test_client()

    register_response = client.post(
        "/register",
        data={
            "full_name": "Ana Test",
            "email": "ana@test.local",
            "password": "secret123",
            "confirm_password": "secret123",
        },
        follow_redirects=True,
    )
    assert register_response.status_code == 200
    assert b"Contul a fost creat" in register_response.data

    login_response = client.post(
        "/login",
        data={"email": "ana@test.local", "password": "secret123"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    assert b"Autentificare reusita" in login_response.data

    create_incident_response = client.post(
        "/incidents/new",
        data={
            "title": "Groapa mare",
            "description": "Masinile evita brusc zona.",
            "address": "Strada Test 10",
            "category_id": str(category_id),
            "priority": "ridicata",
            "latitude": "44.630100",
            "longitude": "22.650200",
        },
        follow_redirects=True,
    )
    assert create_incident_response.status_code == 200
    assert b"Sesizarea a fost trimisa" in create_incident_response.data

    with app.app_context():
        incident = Incident.query.filter_by(title="Groapa mare").first()
        citizen = User.query.filter_by(email="ana@test.local").first()
        assert incident is not None
        assert citizen is not None
        assert incident.created_by_id == citizen.id
        assert incident.assigned_department_id == department_id
        incident_id = incident.id
        citizen_id = citizen.id

    client.post("/logout", follow_redirects=True)

    operator_login_response = client.post(
        "/login",
        data={"email": "operator@test.local", "password": "operator123"},
        follow_redirects=True,
    )
    assert operator_login_response.status_code == 200

    update_response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "status": "in_verificare",
            "assigned_department_id": str(department_id),
            "message": "Preluam cazul pentru verificare in teren.",
        },
        follow_redirects=True,
    )
    assert update_response.status_code == 200
    assert b"Sesizarea a fost actualizata" in update_response.data

    client.post("/logout", follow_redirects=True)
    client.post(
        "/login",
        data={"email": "ana@test.local", "password": "secret123"},
        follow_redirects=True,
    )

    unread_response = client.get("/api/notifications/unread-count")
    assert unread_response.status_code == 200
    assert unread_response.json["unread_count"] >= 1

    with app.app_context():
        notifications = Notification.query.filter_by(user_id=citizen_id).all()
        assert len(notifications) >= 1

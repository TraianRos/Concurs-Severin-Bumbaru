from io import BytesIO
from pathlib import Path
from tempfile import mkdtemp

from app import create_app
from app.extensions import db
from app.models import Category, Department, Incident, Notification, User


def create_test_app():
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    app.instance_path = mkdtemp(prefix="incident-photo-tests-")
    return app


def seed_reference_data():
    roads_department = Department(
        name="Serviciul Drumuri",
        description="Probleme de carosabil.",
        contact_email="drumuri@test.local",
    )
    parks_department = Department(
        name="Serviciul Spatii Verzi",
        description="Probleme legate de copaci si vegetatie.",
        contact_email="spatii-verzi@test.local",
    )
    db.session.add_all([roads_department, parks_department])
    db.session.flush()

    pothole_category = Category(
        name="Groapa",
        description="Groapa in asfalt.",
        default_department_id=roads_department.id,
    )
    tree_category = Category(
        name="Copac cazut",
        description="Probleme cu arborii din oras.",
        default_department_id=parks_department.id,
    )
    db.session.add_all([pothole_category, tree_category])
    db.session.flush()

    operator_roads = User(
        full_name="Operator Drumuri",
        email="operator-drumuri@test.local",
        role="operator",
        department_id=roads_department.id,
    )
    operator_roads.set_password("operator123")

    operator_parks = User(
        full_name="Operator Spatii Verzi",
        email="operator-spatii@test.local",
        role="operator",
        department_id=parks_department.id,
    )
    operator_parks.set_password("operator123")

    dispatcher = User(
        full_name="Dispecer Test",
        email="dispatcher@test.local",
        role="dispatcher",
    )
    dispatcher.set_password("dispatcher123")

    admin = User(
        full_name="Admin Test",
        email="admin@test.local",
        role="admin",
    )
    admin.set_password("admin123")

    db.session.add_all([operator_roads, operator_parks, dispatcher, admin])
    db.session.commit()

    return {
        "departments": {
            "roads": roads_department.id,
            "parks": parks_department.id,
        },
        "categories": {
            "pothole": pothole_category.id,
            "tree": tree_category.id,
        },
    }


def make_fake_jpeg(*, width: int = 16, height: int = 12, total_size: int | None = None) -> bytes:
    app0_segment = (
        b"\xff\xe0"
        + (16).to_bytes(2, "big")
        + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    )
    sof0_segment = (
        b"\xff\xc0"
        + (17).to_bytes(2, "big")
        + b"\x08"
        + height.to_bytes(2, "big")
        + width.to_bytes(2, "big")
        + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00"
    )
    sos_segment = b"\xff\xda" + (12).to_bytes(2, "big") + b"\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00"
    header = b"\xff\xd8" + app0_segment + sof0_segment + sos_segment
    footer = b"\xff\xd9"

    if total_size is None:
        payload = b"\x00" * 64
    else:
        payload_size = total_size - len(header) - len(footer)
        if payload_size < 1:
            raise ValueError("Dimensiunea totala ceruta este prea mica pentru JPEG-ul de test.")
        payload = b"\x00" * payload_size

    return header + payload + footer


def login(client, *, email: str, password: str):
    response = client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )
    assert response.status_code == 200
    return response


def register_and_login_citizen(client, *, full_name: str, email: str):
    register_response = client.post(
        "/register",
        data={
            "full_name": full_name,
            "email": email,
            "password": "secret123",
            "confirm_password": "secret123",
        },
        follow_redirects=True,
    )
    assert register_response.status_code == 200

    login(client, email=email, password="secret123")


def create_incident(
    client,
    *,
    category_id: int,
    title: str = "Groapa mare",
    description: str = "Masinile evita brusc zona.",
    address: str = "Strada Test 10",
    priority: str = "ridicata",
    suggested_department_id: int | None = None,
    extra_data: dict | None = None,
):
    payload = {
        "title": title,
        "description": description,
        "address": address,
        "category_id": str(category_id),
        "priority": priority,
        "latitude": "44.630100",
        "longitude": "22.650200",
    }
    if suggested_department_id is not None:
        payload["suggested_department_id"] = str(suggested_department_id)
    if extra_data:
        payload.update(extra_data)

    response = client.post(
        "/incidents/new",
        data=payload,
        follow_redirects=True,
    )
    assert response.status_code == 200
    return response


def assign_incident(client, incident_id: int, department_id: int, *, message: str = "Departamentul este potrivit."):
    response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "assign_department",
            "assigned_department_id": str(department_id),
            "message": message,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    return response


def test_citizen_incident_enters_triage_and_dispatcher_assigns_department():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    create_response = create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Groapa mare",
        suggested_department_id=reference["departments"]["roads"],
    )
    assert b"Sesizarea a fost trimisa" in create_response.data

    with app.app_context():
        incident = Incident.query.filter_by(title="Groapa mare").first()
        assert incident is not None
        assert incident.status == "in_triere"
        assert incident.suggested_department_id == reference["departments"]["roads"]
        assert incident.assigned_department_id is None
        incident_id = incident.id

        dispatcher = User.query.filter_by(email="dispatcher@test.local").first()
        dispatcher_notifications = Notification.query.filter_by(user_id=dispatcher.id).all()
        assert dispatcher_notifications

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")

    assign_response = assign_incident(
        client,
        incident_id,
        reference["departments"]["parks"],
        message="Departamentul de spatii verzi trebuie sa preia cazul.",
    )
    assert b"Sesizarea a fost atribuita departamentului selectat" in assign_response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "noua"
        assert incident.assigned_department_id == reference["departments"]["parks"]
        assert incident.suggested_department_id is None

    client.post("/logout", follow_redirects=True)
    login(client, email="operator-spatii@test.local", password="operator123")
    operator_parks_dashboard = client.get("/dashboard/operator")
    assert operator_parks_dashboard.status_code == 200
    assert b"Groapa mare" in operator_parks_dashboard.data

    client.post("/logout", follow_redirects=True)
    login(client, email="operator-drumuri@test.local", password="operator123")
    operator_roads_dashboard = client.get("/dashboard/operator")
    assert operator_roads_dashboard.status_code == 200
    assert b"Groapa mare" not in operator_roads_dashboard.data


def test_operator_is_isolated_from_other_departments_internal_actions_and_contact_details():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")
    create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Incident izolat",
    )

    with app.app_context():
        incident_id = Incident.query.filter_by(title="Incident izolat").first().id

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")
    assign_incident(client, incident_id, reference["departments"]["roads"])

    client.post("/logout", follow_redirects=True)
    login(client, email="operator-spatii@test.local", password="operator123")

    detail_response = client.get(f"/incidents/{incident_id}")
    assert detail_response.status_code == 200
    assert b"Ana Test" not in detail_response.data
    assert b"ana@test.local" not in detail_response.data
    assert b"Cetatean anonim" in detail_response.data
    assert b"Actualizare operationala" not in detail_response.data
    assert b"Triere si distribuire" not in detail_response.data

    update_response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "set_status",
            "status": "in_verificare",
            "message": "Nu ar trebui sa mearga.",
        },
        follow_redirects=True,
    )
    assert b"Nu ai acces la gestionarea acestei sesizari" in update_response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "noua"


def test_operator_can_return_incident_to_triage_with_note():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")
    create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Sesizare irelevanta",
    )

    with app.app_context():
        incident_id = Incident.query.filter_by(title="Sesizare irelevanta").first().id

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")
    assign_incident(client, incident_id, reference["departments"]["roads"])
    client.post("/logout", follow_redirects=True)

    login(client, email="operator-drumuri@test.local", password="operator123")
    return_response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "mark_irrelevant",
            "message": "Problema tine de alt flux si trebuie retriata.",
        },
        follow_redirects=True,
    )
    assert b"Sesizarea a fost retrimisa spre triere" in return_response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "in_triere"

    operator_dashboard = client.get("/dashboard/operator")
    assert b"Sesizare irelevanta" not in operator_dashboard.data

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")
    dispatcher_dashboard = client.get("/dashboard/dispatcher")
    assert dispatcher_dashboard.status_code == 200
    assert b"Sesizare irelevanta" in dispatcher_dashboard.data


def test_dispatcher_can_reject_department_suggestion_and_reject_incident():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")
    create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Sugestie gresita",
        suggested_department_id=reference["departments"]["roads"],
    )

    with app.app_context():
        incident_id = Incident.query.filter_by(title="Sugestie gresita").first().id

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")

    reject_suggestion_response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "reject_suggestion",
            "message": "Departamentul sugerat nu corespunde descrierii.",
        },
        follow_redirects=True,
    )
    assert b"Sugestia de departament a fost respinsa" in reject_suggestion_response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "in_triere"
        assert incident.suggested_department_id is None

    reject_incident_response = client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "reject_incident",
            "message": "Sesizarea este duplicata si nu necesita procesare.",
        },
        follow_redirects=True,
    )
    assert b"Sesizarea a fost respinsa" in reject_incident_response.data

    with app.app_context():
        incident = db.session.get(Incident, incident_id)
        assert incident.status == "respinsa"


def test_photo_visibility_respects_dispatcher_selection_and_department_scope():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    upload_response = client.post(
        "/incidents/new",
        data={
            "title": "Groapa cu poze",
            "description": "Am atasat cateva fotografii.",
            "address": "Strada Foto 10",
            "category_id": str(reference["categories"]["pothole"]),
            "priority": "ridicata",
            "latitude": "44.630100",
            "longitude": "22.650200",
            "photo_processing_status": "processed-jpeg-v1",
            "photos": [
                (BytesIO(make_fake_jpeg(width=1280, height=720)), "teren-1.jpg", "image/jpeg"),
                (BytesIO(make_fake_jpeg(width=960, height=640)), "teren-2.jpeg", "image/jpeg"),
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert upload_response.status_code == 200
    assert b"Sesizarea a fost trimisa" in upload_response.data

    with app.app_context():
        incident = Incident.query.filter_by(title="Groapa cu poze").first()
        assert incident is not None
        assert len(incident.photos) == 2
        incident_id = incident.id
        first_photo_id = incident.photos[0].id
        second_photo_id = incident.photos[1].id
        first_photo_url = f"/incidents/{incident_id}/photos/{first_photo_id}"
        second_photo_url = f"/incidents/{incident_id}/photos/{second_photo_id}"

        first_photo_path = (
            Path(app.instance_path)
            / app.config["PHOTO_UPLOAD_SUBDIR"]
            / str(incident.id)
            / incident.photos[0].stored_name
        )
        assert first_photo_path.is_file()

    assert client.get(first_photo_url).status_code == 200
    assert client.get(second_photo_url).status_code == 200

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")
    assign_incident(client, incident_id, reference["departments"]["roads"])

    pertinence_response = client.post(
        f"/incidents/{incident_id}/photos/pertinence",
        data={
            "pertinent_photo_ids": [str(first_photo_id)],
            "message": "Doar prima fotografie este utila pentru departamentul de drumuri.",
        },
        follow_redirects=True,
    )
    assert b"Selectia fotografiilor pertinente a fost actualizata" in pertinence_response.data

    client.post("/logout", follow_redirects=True)
    login(client, email="operator-drumuri@test.local", password="operator123")
    detail_response = client.get(f"/incidents/{incident_id}")
    assert detail_response.status_code == 200
    assert first_photo_url.encode() in detail_response.data
    assert second_photo_url.encode() not in detail_response.data
    assert client.get(first_photo_url).status_code == 200
    assert client.get(second_photo_url).status_code == 404

    client.post("/logout", follow_redirects=True)
    login(client, email="operator-spatii@test.local", password="operator123")
    assert client.get(first_photo_url).status_code == 404
    assert client.get(second_photo_url).status_code == 404

    client.post("/logout", follow_redirects=True)
    login(client, email="admin@test.local", password="admin123")
    assert client.get(first_photo_url).status_code == 200
    assert client.get(second_photo_url).status_code == 200


def test_citizen_sees_anonymized_identity_for_other_users_and_public_history_only():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")
    create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Iluminat lipsa",
        description="Zona este foarte intunecata noaptea.",
        address="Strada Luminii 7",
        priority="medie",
    )

    with app.app_context():
        incident_id = Incident.query.filter_by(title="Iluminat lipsa").first().id

    client.post("/logout", follow_redirects=True)
    login(client, email="dispatcher@test.local", password="dispatcher123")
    assign_incident(client, incident_id, reference["departments"]["roads"])
    client.post("/logout", follow_redirects=True)

    login(client, email="operator-drumuri@test.local", password="operator123")
    client.post(
        f"/incidents/{incident_id}/update",
        data={
            "action": "set_status",
            "status": "in_verificare",
            "message": "Trimitem o echipa pentru verificare in teren.",
        },
        follow_redirects=True,
    )
    client.post("/logout", follow_redirects=True)

    register_and_login_citizen(client, full_name="Maria Test", email="maria@test.local")
    detail_response = client.get(f"/incidents/{incident_id}")
    assert detail_response.status_code == 200
    assert b"Ana Test" not in detail_response.data
    assert b"Operator Drumuri" not in detail_response.data
    assert b"ana@test.local" not in detail_response.data
    assert b"Trimitem o echipa pentru verificare in teren." not in detail_response.data
    assert b"Cetatean anonim" in detail_response.data
    assert b"Platforma" in detail_response.data


def test_map_markers_hide_resolved_and_rejected_incidents():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

        citizen = User(
            full_name="Ana Test",
            email="ana@test.local",
            role="citizen",
        )
        citizen.set_password("secret123")
        db.session.add(citizen)
        db.session.flush()

        visible_incident = Incident(
            title="Groapa activa",
            description="Inca necesita interventie.",
            address="Strada Test 1",
            latitude=44.630100,
            longitude=22.650200,
            priority="medie",
            status="noua",
            created_by_id=citizen.id,
            category_id=reference["categories"]["pothole"],
            suggested_department_id=None,
            assigned_department_id=reference["departments"]["roads"],
        )
        resolved_incident = Incident(
            title="Sesizare rezolvata",
            description="A fost deja inchisa.",
            address="Strada Test 2",
            latitude=44.631100,
            longitude=22.651200,
            priority="medie",
            status="rezolvata",
            created_by_id=citizen.id,
            category_id=reference["categories"]["pothole"],
            suggested_department_id=None,
            assigned_department_id=reference["departments"]["roads"],
        )
        rejected_incident = Incident(
            title="Sesizare respinsa",
            description="Nu trebuie sa mai apara pe harta.",
            address="Strada Test 3",
            latitude=44.632100,
            longitude=22.652200,
            priority="medie",
            status="respinsa",
            created_by_id=citizen.id,
            category_id=reference["categories"]["pothole"],
            suggested_department_id=None,
            assigned_department_id=reference["departments"]["roads"],
        )

        db.session.add_all([visible_incident, resolved_incident, rejected_incident])
        db.session.commit()

    client = app.test_client()
    login(client, email="ana@test.local", password="secret123")

    markers_response = client.get("/api/incidents/markers")
    assert markers_response.status_code == 200

    marker_titles = {marker["title"] for marker in markers_response.json["markers"]}
    assert "Groapa activa" in marker_titles
    assert "Sesizare rezolvata" not in marker_titles
    assert "Sesizare respinsa" not in marker_titles


def test_incident_creation_accepts_department_suggestion_different_from_category_default():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    response = create_incident(
        client,
        category_id=reference["categories"]["pothole"],
        title="Sugestie diferita de implicita",
        suggested_department_id=reference["departments"]["parks"],
    )

    assert b"Sesizarea a fost trimisa" in response.data

    with app.app_context():
        incident = Incident.query.filter_by(title="Sugestie diferita de implicita").first()
        assert incident is not None
        assert incident.status == "in_triere"
        assert incident.suggested_department_id == reference["departments"]["parks"]
        assert incident.assigned_department_id is None


def test_admin_can_create_umbrella_category_without_default_department():
    app = create_test_app()

    with app.app_context():
        seed_reference_data()

    client = app.test_client()
    login(client, email="admin@test.local", password="admin123")

    response = client.post(
        "/admin/categories",
        data={
            "name": "Problema generala",
            "description": "Categorie umbrela pentru sesizari care trebuie triate manual.",
            "default_department_id": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Categoria a fost creata." in response.data

    with app.app_context():
        category = Category.query.filter_by(name="Problema generala").first()
        assert category is not None
        assert category.default_department_id is None


def test_incident_photo_upload_rejects_more_than_three_files():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    response = client.post(
        "/incidents/new",
        data={
            "title": "Prea multe poze",
            "description": "Selectie prea mare.",
            "address": "Strada Foto 11",
            "category_id": str(reference["categories"]["pothole"]),
            "priority": "medie",
            "latitude": "44.630100",
            "longitude": "22.650200",
            "photo_processing_status": "processed-jpeg-v1",
            "photos": [
                (BytesIO(make_fake_jpeg()), "1.jpg", "image/jpeg"),
                (BytesIO(make_fake_jpeg()), "2.jpg", "image/jpeg"),
                (BytesIO(make_fake_jpeg()), "3.jpg", "image/jpeg"),
                (BytesIO(make_fake_jpeg()), "4.jpg", "image/jpeg"),
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Poti incarca maximum 3 fotografii." in response.data


def test_incident_photo_upload_rejects_oversized_photo():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    oversized_jpeg = make_fake_jpeg(total_size=(5 * 1024 * 1024) + 512)
    response = client.post(
        "/incidents/new",
        data={
            "title": "Poza prea mare",
            "description": "Fisierul ramane prea mare dupa compresie.",
            "address": "Strada Foto 12",
            "category_id": str(reference["categories"]["pothole"]),
            "priority": "medie",
            "latitude": "44.630100",
            "longitude": "22.650200",
            "photo_processing_status": "processed-jpeg-v1",
            "photos": [(BytesIO(oversized_jpeg), "mare.jpg", "image/jpeg")],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Una dintre fotografii depaseste limita de 5 MB dupa compresie." in response.data


def test_incident_photo_upload_rejects_invalid_photo_signature():
    app = create_test_app()

    with app.app_context():
        reference = seed_reference_data()

    client = app.test_client()
    register_and_login_citizen(client, full_name="Ana Test", email="ana@test.local")

    response = client.post(
        "/incidents/new",
        data={
            "title": "Fisier invalid",
            "description": "Semnatura nu este JPEG.",
            "address": "Strada Foto 13",
            "category_id": str(reference["categories"]["pothole"]),
            "priority": "medie",
            "latitude": "44.630100",
            "longitude": "22.650200",
            "photo_processing_status": "processed-jpeg-v1",
            "photos": [(BytesIO(b"not-a-jpeg"), "fals.jpg", "image/jpeg")],
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Una dintre fotografii nu are o semnatura JPEG valida." in response.data

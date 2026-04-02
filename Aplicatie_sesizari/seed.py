from app import create_app
from app.extensions import db
from app.models import Category, Department, Incident, Notification, User
from app.repositories.incident_repository import IncidentRepository

app = create_app()


with app.app_context():
    db.create_all()

    if Department.query.count() == 0:
        db.session.add_all(
            [
                Department(
                    name="Serviciul Drumuri",
                    description="Preia gropi, marcaje sterse si alte probleme de carosabil.",
                    contact_email="drumuri@oras.local",
                ),
                Department(
                    name="Iluminat Public",
                    description="Gestioneaza lampi defecte si zone neluminate.",
                    contact_email="iluminat@oras.local",
                ),
                Department(
                    name="Salubritate",
                    description="Preia deseuri abandonate, pubele pline si zone murdare.",
                    contact_email="salubritate@oras.local",
                ),
            ]
        )
        db.session.commit()

    if Category.query.count() == 0:
        departments = {department.name: department for department in Department.query.all()}
        db.session.add_all(
            [
                Category(
                    name="Groapa in carosabil",
                    description="Gropi, asfalt degradat, capace lipsa.",
                    default_department_id=departments["Serviciul Drumuri"].id,
                ),
                Category(
                    name="Iluminat defect",
                    description="Bec ars, stalp cazut, zona intunecata.",
                    default_department_id=departments["Iluminat Public"].id,
                ),
                Category(
                    name="Deseuri abandonate",
                    description="Moloz, gunoi menajer sau vegetatie lasata pe domeniul public.",
                    default_department_id=departments["Salubritate"].id,
                ),
            ]
        )
        db.session.commit()

    if User.query.count() == 0:
        departments = {department.name: department for department in Department.query.all()}

        admin = User(full_name="Admin Local", email="admin@oras.local", role="admin")
        admin.set_password("admin123")

        operator = User(
            full_name="Operator Drumuri",
            email="operator@oras.local",
            role="operator",
            department_id=departments["Serviciul Drumuri"].id,
        )
        operator.set_password("operator123")

        citizen = User(full_name="Mara Popescu", email="cetatean@oras.local", role="citizen")
        citizen.set_password("cetatean123")

        db.session.add_all([admin, operator, citizen])
        db.session.commit()

    if Incident.query.count() == 0:
        citizen = User.query.filter_by(email="cetatean@oras.local").first()
        categories = {category.name: category for category in Category.query.all()}
        incident_repository = IncidentRepository()

        incident = incident_repository.create(
            title="Groapa mare langa trecerea de pietoni",
            description="Masinile ocolesc brusc si devine periculos pentru pietoni.",
            address="Strada Independentei, langa Scoala 5",
            latitude=44.6369,
            longitude=22.6597,
            priority="ridicata",
            status="noua",
            created_by_id=citizen.id,
            category_id=categories["Groapa in carosabil"].id,
            assigned_department_id=categories["Groapa in carosabil"].default_department_id,
        )
        incident_repository.create_update(
            incident_id=incident.id,
            author_id=citizen.id,
            message="Sesizarea initiala a fost trimisa de cetatean.",
            new_status="noua",
            new_department_id=incident.assigned_department_id,
        )
        db.session.add(
            Notification(
                user_id=citizen.id,
                incident_id=incident.id,
                message="Sesizarea ta a fost inregistrata.",
                is_read=False,
            )
        )
        db.session.commit()

    print("Aplicatia de sesizari are baza de date pregatita.")

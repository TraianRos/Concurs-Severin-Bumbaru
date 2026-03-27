from app.extensions import db
from app.models.entities import Department


class DepartmentRepository:
    def all(self) -> list[Department]:
        return Department.query.order_by(Department.name.asc()).all()

    def count(self) -> int:
        return Department.query.count()

    def find(self, department_id: int) -> Department | None:
        return db.session.get(Department, department_id)

    def find_by_name(self, name: str) -> Department | None:
        return Department.query.filter_by(name=name).first()

    def create(self, name: str, description: str, contact_email: str) -> Department:
        department = Department(name=name, description=description, contact_email=contact_email)
        db.session.add(department)
        db.session.flush()
        return department

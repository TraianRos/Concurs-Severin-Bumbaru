from app.extensions import db
from app.models.entities import User


class UserRepository:
    def find(self, user_id: int) -> User | None:
        return db.session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    def all(self) -> list[User]:
        return User.query.order_by(User.full_name.asc()).all()

    def list_operators(self) -> list[User]:
        return User.query.filter(User.role.in_(["operator", "admin"])).order_by(User.full_name.asc()).all()

    def staff_for_department(self, department_id: int | None) -> list[User]:
        query = User.query.filter(User.role.in_(["operator", "admin"]))
        if department_id is not None:
            query = query.filter((User.department_id == department_id) | (User.role == "admin"))
        return query.order_by(User.full_name.asc()).all()

    def create(
        self,
        full_name: str,
        email: str,
        password: str,
        role: str = "citizen",
        department_id: int | None = None,
    ) -> User:
        user = User(full_name=full_name, email=email, role=role, department_id=department_id)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        return user

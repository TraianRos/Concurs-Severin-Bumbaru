from app.extensions import db
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository, department_repository: DepartmentRepository) -> None:
        self.user_repository = user_repository
        self.department_repository = department_repository

    def register_citizen(self, payload: dict) -> dict:
        full_name = payload.get("full_name", "").strip()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        confirm_password = payload.get("confirm_password", "")

        if not full_name or not email or not password:
            return {"ok": False, "message": "Completeaza toate campurile obligatorii."}
        if "@" not in email:
            return {"ok": False, "message": "Adresa de email nu pare valida."}
        if len(password) < 6:
            return {"ok": False, "message": "Parola trebuie sa aiba cel putin 6 caractere."}
        if password != confirm_password:
            return {"ok": False, "message": "Parolele nu coincid."}
        if self.user_repository.find_by_email(email):
            return {"ok": False, "message": "Exista deja un cont cu acest email."}

        user = self.user_repository.create(full_name, email, password, role="citizen")
        db.session.commit()
        return {"ok": True, "message": "Contul a fost creat. Acum te poti autentifica.", "user": user}

    def authenticate(self, email: str, password: str) -> dict:
        normalized_email = email.strip().lower()
        user = self.user_repository.find_by_email(normalized_email)
        if user is None or not user.check_password(password):
            return {"ok": False, "message": "Email sau parola incorecte."}
        return {"ok": True, "message": "Autentificare reusita.", "user": user}

    def create_operator(self, payload: dict) -> dict:
        full_name = payload.get("full_name", "").strip()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        department_id = payload.get("department_id", "").strip()

        if not full_name or not email or not password or not department_id:
            return {"ok": False, "message": "Completeaza toate campurile pentru operator."}
        if "@" not in email:
            return {"ok": False, "message": "Emailul operatorului nu este valid."}
        if self.user_repository.find_by_email(email):
            return {"ok": False, "message": "Exista deja un utilizator cu acest email."}
        if not department_id.isdigit():
            return {"ok": False, "message": "Departamentul selectat nu este valid."}

        department = self.department_repository.find(int(department_id))
        if department is None:
            return {"ok": False, "message": "Departamentul nu exista."}

        self.user_repository.create(
            full_name=full_name,
            email=email,
            password=password,
            role="operator",
            department_id=department.id,
        )
        db.session.commit()
        return {"ok": True, "message": "Operatorul a fost creat."}

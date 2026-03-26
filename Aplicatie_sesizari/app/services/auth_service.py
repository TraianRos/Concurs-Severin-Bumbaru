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
            return {"ok": False, "message": "Completează toate câmpurile obligatorii."}
        if "@" not in email:
            return {"ok": False, "message": "Adresa de email nu pare validă."}
        if len(password) < 6:
            return {"ok": False, "message": "Parola trebuie sa aiba cel putin 6 caractere."}
        if password != confirm_password:
            return {"ok": False, "message": "Parolele nu coincid."}
        if self.user_repository.find_by_email(email):
            return {"ok": False, "message": "Există deja un cont cu acest email."}

        user = self.user_repository.create(full_name, email, password, role="citizen")
        db.session.commit()
        return {"ok": True, "message": "Contul a fost creat. Acum te poți autentifica.", "user": user}

    def authenticate(self, email: str, password: str) -> dict:
        normalized_email = email.strip().lower()
        user = self.user_repository.find_by_email(normalized_email)
        if user is None or not user.check_password(password):
            return {"ok": False, "message": "Email sau parola incorecte."}
        return {"ok": True, "message": "Autentificare reușită.", "user": user}

    def create_operator(self, payload: dict) -> dict:
        return self.create_staff(payload)

    def create_staff(self, payload: dict) -> dict:
        full_name = payload.get("full_name", "").strip()
        email = payload.get("email", "").strip().lower()
        password = payload.get("password", "")
        role = payload.get("role", "operator").strip()
        department_id = payload.get("department_id", "").strip()

        if not full_name or not email or not password:
            return {"ok": False, "message": "Completează toate câmpurile pentru utilizatorul intern."}
        if "@" not in email:
            return {"ok": False, "message": "Emailul utilizatorului nu este valid."}
        if self.user_repository.find_by_email(email):
            return {"ok": False, "message": "Există deja un utilizator cu acest email."}
        if role not in ["operator", "dispatcher"]:
            return {"ok": False, "message": "Rolul selectat nu este valid."}

        resolved_department_id = None
        if role == "operator":
            if not department_id.isdigit():
                return {"ok": False, "message": "Departamentul selectat nu este valid."}

            department = self.department_repository.find(int(department_id))
            if department is None:
                return {"ok": False, "message": "Departamentul nu există."}
            resolved_department_id = department.id

        self.user_repository.create(
            full_name=full_name,
            email=email,
            password=password,
            role=role,
            department_id=resolved_department_id,
        )
        db.session.commit()
        if role == "dispatcher":
            return {"ok": True, "message": "Dispecerul a fost creat."}
        return {"ok": True, "message": "Operatorul a fost creat."}

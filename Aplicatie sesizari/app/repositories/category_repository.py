from app.extensions import db
from app.models.entities import Category


class CategoryRepository:
    def all(self) -> list[Category]:
        return Category.query.order_by(Category.name.asc()).all()

    def count(self) -> int:
        return Category.query.count()

    def find(self, category_id: int) -> Category | None:
        return db.session.get(Category, category_id)

    def find_by_name(self, name: str) -> Category | None:
        return Category.query.filter_by(name=name).first()

    def create(self, name: str, description: str, default_department_id: int | None) -> Category:
        category = Category(
            name=name,
            description=description,
            default_department_id=default_department_id,
        )
        db.session.add(category)
        db.session.flush()
        return category

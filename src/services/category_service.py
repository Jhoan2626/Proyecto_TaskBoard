from src.models import db, Category

class CategoryService:

    @staticmethod
    def create_category(user_id: int, name: str) -> tuple:
        """
        Crea una nueva categoría para el usuario autenticado (HU-08).
        Valida nombre no vacío y unicidad por usuario.
        """
        if not name or not name.strip():
            return None, 'El nombre de la categoría no puede estar vacío.'

        cleaned_name = name.strip()

        existing = Category.query.filter_by(user_id=user_id, name=cleaned_name).first()
        if existing:
            return None, f"Ya existe una categoría con el nombre '{cleaned_name}'."

        category = Category(user_id=user_id, name=cleaned_name)
        db.session.add(category)
        db.session.commit()
        return category, None

    @staticmethod
    def get_user_categories(user_id: int) -> list:
        """Lista las categorías del usuario autenticado (HU-08)."""
        return Category.query.filter_by(user_id=user_id).order_by(Category.name).all()

    @staticmethod
    def get_category_by_id(user_id: int, category_id: int) -> tuple:
        """Obtiene una categoría verificando propiedad (Principio VII)."""
        cat = db.session.get(Category, category_id)
        if not cat:
            return None, 'Categoría no encontrada.'
        if cat.user_id != user_id:
            return None, 'No tiene permiso para acceder a esta categoría.'
        return cat, None

    @staticmethod
    def delete_category(user_id: int, category_id: int) -> tuple:
        """
        Elimina una categoría. Las tareas asociadas quedan con category_id=NULL
        (gestionado por ON DELETE SET NULL en la FK).
        Verifica propiedad (Principio VII).
        """
        cat, error = CategoryService.get_category_by_id(user_id, category_id)
        if error:
            return None, error

        # Fallback explícito por si SQLite no tiene PRAGMA foreign_keys=ON
        from src.models import Task
        Task.query.filter_by(category_id=category_id).update({'category_id': None})

        db.session.delete(cat)
        db.session.commit()
        return cat, None


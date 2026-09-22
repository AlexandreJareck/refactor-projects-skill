from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from database import db
from errors import APIError
from models.category import Category
from models.task import Task
from utils.helpers import DEFAULT_COLOR


def _category_or_404(category_id):
    category = db.session.get(Category, category_id)
    if not category:
        raise APIError("Categoria não encontrada", 404)
    return category


def list_categories():
    rows = db.session.execute(
        select(Category, func.count(Task.id))
        .outerjoin(Task, Task.category_id == Category.id)
        .group_by(Category.id)
    ).all()
    result = []
    for category, task_count in rows:
        data = category.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise APIError("Dados inválidos", 400)
    if not data.get("name"):
        raise APIError("Nome é obrigatório", 400)
    category = Category(
        name=data["name"],
        description=data.get("description", ""),
        color=data.get("color", DEFAULT_COLOR),
    )
    try:
        db.session.add(category)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao criar categoria", 500) from error
    return category.to_dict()


def update_category(category_id, data):
    category = _category_or_404(category_id)
    if not data:
        raise APIError("Dados inválidos", 400)
    for field in ("name", "description", "color"):
        if field in data:
            setattr(category, field, data[field])
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao atualizar", 500) from error
    return category.to_dict()


def delete_category(category_id):
    category = _category_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao deletar", 500) from error
    return {"message": "Categoria deletada"}


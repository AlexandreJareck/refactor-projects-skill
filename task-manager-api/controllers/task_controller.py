from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from database import db
from errors import APIError
from models.category import Category
from models.task import Task
from models.user import User
from utils.datetime_utils import utc_now
from utils.helpers import DEFAULT_PRIORITY, process_task_data, validate_priority


def _task_or_404(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise APIError("Task não encontrada", 404)
    return task


def _check_relations(user_id=None, category_id=None):
    if user_id and not db.session.get(User, user_id):
        raise APIError("Usuário não encontrado", 404)
    if category_id and not db.session.get(Category, category_id):
        raise APIError("Categoria não encontrada", 404)


def _serialize_list_item(task, now):
    data = task.to_dict()
    data["overdue"] = task.is_overdue(now)
    data["user_name"] = task.user.name if task.user else None
    data["category_name"] = task.category.name if task.category else None
    return data


def list_tasks():
    tasks = db.session.scalars(
        select(Task).options(joinedload(Task.user), joinedload(Task.category))
    ).all()
    now = utc_now()
    return [_serialize_list_item(task, now) for task in tasks]


def get_task(task_id):
    task = _task_or_404(task_id)
    data = task.to_dict()
    data["overdue"] = task.is_overdue()
    return data


def create_task(data):
    if not data:
        raise APIError("Dados inválidos", 400)
    if not data.get("title"):
        raise APIError("Título é obrigatório", 400)

    values = {
        "title": data.get("title"),
        "description": data.get("description", ""),
        "status": data.get("status", "pending"),
        "priority": data.get("priority", DEFAULT_PRIORITY),
    }
    for optional in ("due_date", "tags"):
        if optional in data:
            values[optional] = data[optional]
    values, error = process_task_data(values)
    if error:
        raise APIError(error, 400)

    user_id = data.get("user_id")
    category_id = data.get("category_id")
    _check_relations(user_id, category_id)
    task = Task(**values, user_id=user_id, category_id=category_id)

    try:
        db.session.add(task)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao criar task", 500) from error
    return task.to_dict()


def update_task(task_id, data):
    task = _task_or_404(task_id)
    if not data:
        raise APIError("Dados inválidos", 400)

    values, error = process_task_data(data)
    if error:
        raise APIError(error.replace(". Use YYYY-MM-DD", ""), 400)
    if "user_id" in data:
        _check_relations(user_id=data["user_id"])
        values["user_id"] = data["user_id"]
    if "category_id" in data:
        _check_relations(category_id=data["category_id"])
        values["category_id"] = data["category_id"]
    for field, value in values.items():
        setattr(task, field, value)
    task.updated_at = utc_now()

    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao atualizar", 500) from error
    return task.to_dict()


def delete_task(task_id):
    task = _task_or_404(task_id)
    try:
        db.session.delete(task)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao deletar", 500) from error
    return {"message": "Task deletada com sucesso"}


def search_tasks(arguments):
    statement = select(Task)
    query = arguments.get("q", "")
    status = arguments.get("status", "")
    priority = arguments.get("priority", "")
    user_id = arguments.get("user_id", "")

    if query:
        statement = statement.where(
            or_(Task.title.like(f"%{query}%"), Task.description.like(f"%{query}%"))
        )
    if status:
        statement = statement.where(Task.status == status)
    if priority:
        parsed_priority = validate_priority(priority)
        if parsed_priority is None:
            raise APIError("Prioridade inválida", 400)
        statement = statement.where(Task.priority == parsed_priority)
    if user_id:
        try:
            parsed_user_id = int(user_id)
        except (TypeError, ValueError) as error:
            raise APIError("Usuário inválido", 400) from error
        statement = statement.where(Task.user_id == parsed_user_id)
    return [task.to_dict() for task in db.session.scalars(statement).all()]


def task_stats():
    status_counts = dict(
        db.session.execute(
            select(Task.status, func.count(Task.id)).group_by(Task.status)
        ).all()
    )
    tasks = db.session.scalars(select(Task)).all()
    total = len(tasks)
    done = status_counts.get("done", 0)
    return {
        "total": total,
        "pending": status_counts.get("pending", 0),
        "in_progress": status_counts.get("in_progress", 0),
        "done": done,
        "cancelled": status_counts.get("cancelled", 0),
        "overdue": sum(task.is_overdue() for task in tasks),
        "completion_rate": round((done / total) * 100, 2) if total else 0,
    }


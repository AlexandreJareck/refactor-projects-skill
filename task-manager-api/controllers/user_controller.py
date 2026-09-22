from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from database import db
from errors import APIError
from models.task import Task
from models.user import User
from utils.helpers import MIN_PASSWORD_LENGTH, validate_email, validate_role


def _user_or_404(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise APIError("Usuário não encontrado", 404)
    return user


def list_users():
    rows = db.session.execute(
        select(User, func.count(Task.id))
        .outerjoin(Task, Task.user_id == User.id)
        .group_by(User.id)
    ).all()
    result = []
    for user, task_count in rows:
        data = user.to_dict()
        data["task_count"] = task_count
        result.append(data)
    return result


def get_user(user_id):
    user = _user_or_404(user_id)
    data = user.to_dict()
    data["tasks"] = [
        task.to_dict()
        for task in db.session.scalars(
            select(Task).where(Task.user_id == user_id)
        ).all()
    ]
    return data


def create_user(data):
    if not data:
        raise APIError("Dados inválidos", 400)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")
    if not name:
        raise APIError("Nome é obrigatório", 400)
    if not email:
        raise APIError("Email é obrigatório", 400)
    if not password:
        raise APIError("Senha é obrigatória", 400)
    if not validate_email(email):
        raise APIError("Email inválido", 400)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise APIError("Senha deve ter no mínimo 4 caracteres", 400)
    if db.session.scalar(select(User).where(User.email == email)):
        raise APIError("Email já cadastrado", 409)
    if not validate_role(role):
        raise APIError("Role inválido", 400)

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao criar usuário", 500) from error
    return user.to_dict()


def update_user(user_id, data):
    user = _user_or_404(user_id)
    if not data:
        raise APIError("Dados inválidos", 400)
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        if not validate_email(data["email"]):
            raise APIError("Email inválido", 400)
        existing = db.session.scalar(select(User).where(User.email == data["email"]))
        if existing and existing.id != user_id:
            raise APIError("Email já cadastrado", 409)
        user.email = data["email"]
    if "password" in data:
        if len(data["password"]) < MIN_PASSWORD_LENGTH:
            raise APIError("Senha muito curta", 400)
        user.set_password(data["password"])
    if "role" in data:
        if not validate_role(data["role"]):
            raise APIError("Role inválido", 400)
        user.role = data["role"]
    if "active" in data:
        user.active = data["active"]
    try:
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao atualizar", 500) from error
    return user.to_dict()


def delete_user(user_id):
    user = _user_or_404(user_id)
    try:
        db.session.execute(delete(Task).where(Task.user_id == user_id))
        db.session.delete(user)
        db.session.commit()
    except SQLAlchemyError as error:
        db.session.rollback()
        raise APIError("Erro ao deletar", 500) from error
    return {"message": "Usuário deletado com sucesso"}


def get_user_tasks(user_id):
    _user_or_404(user_id)
    tasks = db.session.scalars(select(Task).where(Task.user_id == user_id)).all()
    result = []
    for task in tasks:
        result.append(
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "created_at": str(task.created_at),
                "due_date": str(task.due_date) if task.due_date else None,
                "overdue": task.is_overdue(),
            }
        )
    return result


def login(data):
    if not data:
        raise APIError("Dados inválidos", 400)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise APIError("Email e senha são obrigatórios", 400)
    user = db.session.scalar(select(User).where(User.email == email))
    if not user or not user.check_password(password):
        raise APIError("Credenciais inválidas", 401)
    if not user.active:
        raise APIError("Usuário inativo", 403)
    if db.session.is_modified(user):
        db.session.commit()
    return {
        "message": "Login realizado com sucesso",
        "user": user.to_dict(),
        "token": "fake-jwt-token-" + str(user.id),
    }


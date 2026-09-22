"""Script para popular o banco com dados iniciais."""

from datetime import timedelta

from sqlalchemy import delete, func, select

from app import app
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.datetime_utils import utc_now


def seed_data():
    with app.app_context():
        db.create_all()
        db.session.execute(delete(Task))
        db.session.execute(delete(User))
        db.session.execute(delete(Category))

        users = [
            User(name="João Silva", email="joao@email.com", role="admin"),
            User(name="Maria Santos", email="maria@email.com", role="user"),
            User(name="Pedro Oliveira", email="pedro@email.com", role="manager"),
        ]
        for user, password in zip(users, ("1234", "abcd", "pass"), strict=True):
            user.set_password(password)
            db.session.add(user)
        db.session.flush()

        categories = [
            Category(name="Backend", description="Tarefas de backend", color="#3498db"),
            Category(name="Frontend", description="Tarefas de frontend", color="#2ecc71"),
            Category(name="DevOps", description="Tarefas de infraestrutura", color="#e74c3c"),
            Category(name="Bug", description="Correção de bugs", color="#e67e22"),
        ]
        db.session.add_all(categories)
        db.session.flush()
        now = utc_now()
        tasks_data = [
            ("Implementar autenticação JWT", "Adicionar autenticação real com JWT", "pending", 1, 0, 0, now - timedelta(days=3), None),
            ("Criar tela de login", "Tela de login responsiva", "in_progress", 2, 1, 1, now + timedelta(days=5), None),
            ("Configurar CI/CD", "Pipeline com GitHub Actions", "done", 2, 2, 2, None, "devops,ci,github"),
            ("Corrigir bug no filtro de busca", "Filtro não funciona com caracteres especiais", "pending", 1, 0, 3, now - timedelta(days=1), None),
            ("Adicionar paginação na API", "Endpoints retornam todos os registros", "pending", 3, 0, 0, now + timedelta(days=10), None),
            ("Escrever testes unitários", "Cobertura mínima de 80%", "pending", 2, 1, 0, None, None),
            ("Documentar API com Swagger", "Gerar documentação automática", "cancelled", 4, 2, 0, None, None),
            ("Refatorar models", "Melhorar organização dos models", "in_progress", 3, 1, 0, None, "refactor,tech-debt"),
            ("Configurar monitoramento", "Prometheus + Grafana", "pending", 4, 2, 2, now + timedelta(days=20), None),
            ("Melhorar validações de input", "Usar marshmallow ou pydantic", "pending", 3, 0, 0, None, "improvement,validation"),
        ]
        db.session.add_all(
            [
                Task(
                    title=title,
                    description=description,
                    status=status,
                    priority=priority,
                    user_id=users[user_index].id,
                    category_id=categories[category_index].id,
                    due_date=due_date,
                    tags=tags,
                )
                for title, description, status, priority, user_index, category_index, due_date, tags in tasks_data
            ]
        )
        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {db.session.scalar(select(func.count(User.id)))} usuários")
        print(f"  {db.session.scalar(select(func.count(Category.id)))} categorias")
        print(f"  {db.session.scalar(select(func.count(Task.id)))} tasks")


if __name__ == "__main__":
    seed_data()

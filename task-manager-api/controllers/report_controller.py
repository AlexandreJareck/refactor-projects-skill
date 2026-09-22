from datetime import timedelta

from sqlalchemy import select

from database import db
from errors import APIError
from models.category import Category
from models.task import Task
from models.user import User
from utils.datetime_utils import utc_now
from utils.helpers import calculate_percentage


def summary_report():
    users = db.session.scalars(select(User)).all()
    categories = db.session.scalars(select(Category)).all()
    tasks = db.session.scalars(select(Task)).all()
    now = utc_now()
    seven_days_ago = now - timedelta(days=7)

    status_counts = {
        status: sum(task.status == status for task in tasks)
        for status in ("pending", "in_progress", "done", "cancelled")
    }
    priority_counts = {
        priority: sum(task.priority == priority for task in tasks)
        for priority in range(1, 6)
    }
    overdue_tasks = [task for task in tasks if task.is_overdue(now)]

    task_counts_by_user = {}
    completed_counts_by_user = {}
    for task in tasks:
        task_counts_by_user[task.user_id] = task_counts_by_user.get(task.user_id, 0) + 1
        if task.status == "done":
            completed_counts_by_user[task.user_id] = (
                completed_counts_by_user.get(task.user_id, 0) + 1
            )

    user_stats = []
    for user in users:
        total = task_counts_by_user.get(user.id, 0)
        completed = completed_counts_by_user.get(user.id, 0)
        user_stats.append(
            {
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": total,
                "completed_tasks": completed,
                "completion_rate": calculate_percentage(completed, total),
            }
        )

    return {
        "generated_at": str(now),
        "overview": {
            "total_tasks": len(tasks),
            "total_users": len(users),
            "total_categories": len(categories),
        },
        "tasks_by_status": status_counts,
        "tasks_by_priority": {
            "critical": priority_counts[1],
            "high": priority_counts[2],
            "medium": priority_counts[3],
            "low": priority_counts[4],
            "minimal": priority_counts[5],
        },
        "overdue": {
            "count": len(overdue_tasks),
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "due_date": str(task.due_date),
                    "days_overdue": (now - task.due_date).days,
                }
                for task in overdue_tasks
            ],
        },
        "recent_activity": {
            "tasks_created_last_7_days": sum(
                task.created_at >= seven_days_ago for task in tasks
            ),
            "tasks_completed_last_7_days": sum(
                task.status == "done" and task.updated_at >= seven_days_ago
                for task in tasks
            ),
        },
        "user_productivity": user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise APIError("Usuário não encontrado", 404)
    tasks = db.session.scalars(select(Task).where(Task.user_id == user_id)).all()
    total = len(tasks)
    status_counts = {
        status: sum(task.status == status for task in tasks)
        for status in ("done", "pending", "in_progress", "cancelled")
    }
    return {
        "user": {"id": user.id, "name": user.name, "email": user.email},
        "statistics": {
            "total_tasks": total,
            **status_counts,
            "overdue": sum(task.is_overdue() for task in tasks),
            "high_priority": sum(task.priority <= 2 for task in tasks),
            "completion_rate": calculate_percentage(status_counts["done"], total),
        },
    }


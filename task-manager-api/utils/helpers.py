import re
from datetime import datetime


VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = "#000000"


def format_date(date_obj):
    return str(date_obj) if date_obj else None


def calculate_percentage(part, total):
    return round((part / total) * 100, 2) if total else 0


def validate_email(email):
    return bool(
        email and re.fullmatch(r"[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+", email)
    )


def parse_date(date_string):
    for date_format in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, date_format)
        except (TypeError, ValueError):
            continue
    return None


def validate_title(title):
    if not title:
        return None, "Título não pode ser vazio"
    title = title.strip()
    if len(title) < MIN_TITLE_LENGTH:
        return None, "Título muito curto"
    if len(title) > MAX_TITLE_LENGTH:
        return None, "Título muito longo"
    return title, None


def validate_status(status):
    return status in VALID_STATUSES


def validate_priority(priority):
    try:
        priority = int(priority)
    except (TypeError, ValueError):
        return None
    return priority if 1 <= priority <= 5 else None


def validate_role(role):
    return role in VALID_ROLES


def process_task_data(data):
    result = {}
    if "title" in data:
        title, error = validate_title(data["title"])
        if error:
            return None, error
        result["title"] = title
    if "description" in data:
        result["description"] = data["description"]
    if "status" in data:
        if not validate_status(data["status"]):
            return None, "Status inválido"
        result["status"] = data["status"]
    if "priority" in data:
        priority = validate_priority(data["priority"])
        if priority is None:
            return None, "Prioridade deve ser entre 1 e 5"
        result["priority"] = priority
    if "due_date" in data:
        if data["due_date"]:
            parsed = parse_date(data["due_date"])
            if not parsed:
                return None, "Formato de data inválido. Use YYYY-MM-DD"
            result["due_date"] = parsed
        else:
            result["due_date"] = None
    if "tags" in data:
        tags = data["tags"]
        result["tags"] = ",".join(tags) if isinstance(tags, list) else tags
    return result, None

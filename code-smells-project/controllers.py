"""Domain workflows, independent of HTTP response construction."""

import math

from werkzeug.security import check_password_hash, generate_password_hash

import models
from constants import ORDER_STATUSES, PRODUCT_CATEGORIES
from errors import APIError


def validate_product(data):
    if not isinstance(data, dict) or not data:
        raise APIError("Dados inválidos")
    for key, label in (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque")):
        if key not in data:
            raise APIError(f"{label} é obrigatório")
    name = data["nome"]
    price = data["preco"]
    stock = data["estoque"]
    category = data.get("categoria", "geral")
    if not isinstance(name, str):
        raise APIError("Nome inválido")
    if len(name) < 2:
        raise APIError("Nome muito curto")
    if len(name) > 200:
        raise APIError("Nome muito longo")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price):
        raise APIError("Preço inválido")
    if price < 0:
        raise APIError("Preço não pode ser negativo")
    if isinstance(stock, bool) or not isinstance(stock, int):
        raise APIError("Estoque inválido")
    if stock < 0:
        raise APIError("Estoque não pode ser negativo")
    if category not in PRODUCT_CATEGORIES:
        raise APIError("Categoria inválida. Válidas: " + str(list(PRODUCT_CATEGORIES)))
    return {
        "nome": name, "descricao": data.get("descricao", ""),
        "preco": price, "estoque": stock, "categoria": category,
    }


def list_products():
    return models.list_products()


def get_product(product_id):
    result = models.get_product(product_id)
    if result is None:
        raise APIError("Produto não encontrado", 404, True)
    return result


def search_products(term, category, minimum, maximum):
    try:
        minimum = float(minimum) if minimum is not None else None
        maximum = float(maximum) if maximum is not None else None
    except ValueError:
        raise APIError("Preço inválido") from None
    if any(value is not None and not math.isfinite(value) for value in (minimum, maximum)):
        raise APIError("Preço inválido")
    return models.search_products(term, category, minimum, maximum)


def create_product(data):
    return models.create_product(validate_product(data))


def update_product(product_id, data):
    if models.get_product(product_id) is None:
        raise APIError("Produto não encontrado", 404)
    models.update_product(product_id, validate_product(data))


def delete_product(product_id):
    if models.get_product(product_id) is None:
        raise APIError("Produto não encontrado", 404)
    models.delete_product(product_id)


def list_users():
    return models.list_users()


def get_user(user_id):
    user = models.get_user(user_id)
    if user is None:
        raise APIError("Usuário não encontrado", 404)
    return user


def create_user(data):
    if not isinstance(data, dict) or not data:
        raise APIError("Dados inválidos")
    name, email, password = (data.get(key) for key in ("nome", "email", "senha"))
    if not all(isinstance(value, str) and value for value in (name, email, password)):
        raise APIError("Nome, email e senha são obrigatórios")
    if models.get_user_credentials(email):
        raise APIError("Email já cadastrado", 409)
    return models.create_user(name, email, generate_password_hash(password))


def login(data):
    if not isinstance(data, dict):
        raise APIError("Email e senha são obrigatórios")
    email, password = data.get("email"), data.get("senha")
    if not isinstance(email, str) or not isinstance(password, str) or not email or not password:
        raise APIError("Email e senha são obrigatórios")
    user = models.get_user_credentials(email)
    if user is None or not check_password_hash(user["senha"], password):
        raise APIError("Email ou senha inválidos", 401, True)
    return {key: user[key] for key in ("id", "nome", "email", "tipo")}


def create_order(data):
    if not isinstance(data, dict) or not data:
        raise APIError("Dados inválidos")
    user_id = data.get("usuario_id")
    items = data.get("itens")
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise APIError("Usuario ID é obrigatório")
    if not isinstance(items, list) or not items:
        raise APIError("Pedido deve ter pelo menos 1 item")
    if models.get_user(user_id) is None:
        raise APIError("Usuário não encontrado", 400, True)
    quantities = {}
    for item in items:
        if not isinstance(item, dict):
            raise APIError("Item inválido", 400, True)
        product_id, quantity = item.get("produto_id"), item.get("quantidade")
        if (not isinstance(product_id, int) or isinstance(product_id, bool) or product_id <= 0
                or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0):
            raise APIError("Item inválido", 400, True)
        quantities[product_id] = quantities.get(product_id, 0) + quantity
    prepared = []
    total = 0
    for product_id, quantity in quantities.items():
        product = models.get_product(product_id)
        if product is None:
            raise APIError(f"Produto {product_id} não encontrado", 400, True)
        if product["estoque"] < quantity:
            raise APIError("Estoque insuficiente para " + product["nome"], 400, True)
        total += product["preco"] * quantity
        prepared.append({"produto_id": product_id, "quantidade": quantity,
                         "preco_unitario": product["preco"]})
    try:
        order_id = models.create_order(user_id, prepared, total)
    except ValueError:
        raise APIError("Estoque insuficiente", 400, True) from None
    return {"pedido_id": order_id, "total": total}


def list_orders(user_id=None):
    return models.list_orders(user_id)


def update_order_status(order_id, data):
    status = data.get("status") if isinstance(data, dict) else None
    if status not in ORDER_STATUSES:
        raise APIError("Status inválido")
    if not models.update_order_status(order_id, status):
        raise APIError("Pedido não encontrado", 404)


def sales_report():
    order_count, gross, statuses = models.sales_totals()
    if gross > 10000:
        discount = gross * 0.10
    elif gross > 5000:
        discount = gross * 0.05
    elif gross > 1000:
        discount = gross * 0.02
    else:
        discount = 0
    return {
        "total_pedidos": order_count,
        "faturamento_bruto": round(gross, 2),
        "desconto_aplicavel": round(discount, 2),
        "faturamento_liquido": round(gross - discount, 2),
        "pedidos_pendentes": statuses.get("pendente", 0),
        "pedidos_aprovados": statuses.get("aprovado", 0),
        "pedidos_cancelados": statuses.get("cancelado", 0),
        "ticket_medio": round(gross / order_count, 2) if order_count else 0,
    }


def health():
    return {"status": "ok", "database": "connected",
            "counts": models.health_counts(), "versao": "1.0.0"}

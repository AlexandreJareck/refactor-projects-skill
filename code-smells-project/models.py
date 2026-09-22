"""Parameterized persistence and public data projections."""

from database import get_db


PRODUCT_FIELDS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"
USER_FIELDS = "id, nome, email, tipo, criado_em"


def product(row):
    return dict(row) if row else None


def list_products():
    return [product(row) for row in get_db().execute(f"SELECT {PRODUCT_FIELDS} FROM produtos")]


def get_product(product_id):
    return product(get_db().execute(
        f"SELECT {PRODUCT_FIELDS} FROM produtos WHERE id = ?", (product_id,)
    ).fetchone())


def search_products(term, category, minimum, maximum):
    query = f"SELECT {PRODUCT_FIELDS} FROM produtos WHERE 1 = 1"
    params = []
    if term:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend((f"%{term}%", f"%{term}%"))
    if category:
        query += " AND categoria = ?"
        params.append(category)
    if minimum is not None:
        query += " AND preco >= ?"
        params.append(minimum)
    if maximum is not None:
        query += " AND preco <= ?"
        params.append(maximum)
    return [product(row) for row in get_db().execute(query, params)]


def create_product(data):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (data["nome"], data["descricao"], data["preco"], data["estoque"], data["categoria"]),
        )
    return cursor.lastrowid


def update_product(product_id, data):
    db = get_db()
    with db:
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (data["nome"], data["descricao"], data["preco"], data["estoque"], data["categoria"], product_id),
        )


def delete_product(product_id):
    db = get_db()
    with db:
        db.execute("DELETE FROM produtos WHERE id = ?", (product_id,))


def list_users():
    return [dict(row) for row in get_db().execute(f"SELECT {USER_FIELDS} FROM usuarios")]


def get_user(user_id):
    row = get_db().execute(f"SELECT {USER_FIELDS} FROM usuarios WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_credentials(email):
    return get_db().execute(
        "SELECT id, nome, email, tipo, senha FROM usuarios WHERE email = ?", (email,)
    ).fetchone()


def create_user(name, email, password_hash):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, "cliente"),
        )
    return cursor.lastrowid


def create_order(user_id, items, total):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (user_id, "pendente", total),
        )
        order_id = cursor.lastrowid
        for item in items:
            changed = db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            ).rowcount
            if changed != 1:
                raise ValueError("Estoque insuficiente")
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (order_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
        db.commit()
        return order_id
    except Exception:
        db.rollback()
        raise


def list_orders(user_id=None):
    query = """
        SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
               i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
        FROM pedidos AS p
        LEFT JOIN itens_pedido AS i ON i.pedido_id = p.id
        LEFT JOIN produtos AS pr ON pr.id = i.produto_id
    """
    params = ()
    if user_id is not None:
        query += " WHERE p.usuario_id = ?"
        params = (user_id,)
    query += " ORDER BY p.id, i.id"
    orders = {}
    for row in get_db().execute(query, params):
        order = orders.setdefault(row["id"], {
            "id": row["id"], "usuario_id": row["usuario_id"],
            "status": row["status"], "total": row["total"],
            "criado_em": row["criado_em"], "itens": [],
        })
        if row["produto_id"] is not None:
            order["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(orders.values())


def update_order_status(order_id, status):
    db = get_db()
    with db:
        return db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (status, order_id)
        ).rowcount == 1


def sales_totals():
    db = get_db()
    totals = db.execute("SELECT COUNT(*) AS total_pedidos, COALESCE(SUM(total), 0) AS faturamento FROM pedidos").fetchone()
    statuses = dict(db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
    return totals["total_pedidos"], totals["faturamento"], statuses


def health_counts():
    db = get_db()
    return {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("produtos", "usuarios", "pedidos")}

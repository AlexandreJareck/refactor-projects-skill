"""HTTP routes and JSON presentation."""

from flask import Blueprint, jsonify, request

import controllers


api = Blueprint("api", __name__)


@api.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja", "versao": "1.0.0",
        "endpoints": {
            "produtos": "/produtos", "usuarios": "/usuarios",
            "pedidos": "/pedidos", "login": "/login",
            "relatorios": "/relatorios/vendas", "health": "/health",
        },
    })


@api.get("/produtos")
def list_products():
    return jsonify({"dados": controllers.list_products(), "sucesso": True})


@api.get("/produtos/busca")
def search_products():
    results = controllers.search_products(
        request.args.get("q", ""), request.args.get("categoria"),
        request.args.get("preco_min"), request.args.get("preco_max"),
    )
    return jsonify({"dados": results, "total": len(results), "sucesso": True})


@api.get("/produtos/<int:id>")
def get_product(id):
    return jsonify({"dados": controllers.get_product(id), "sucesso": True})


@api.post("/produtos")
def create_product():
    product_id = controllers.create_product(request.get_json(silent=True))
    return jsonify({"dados": {"id": product_id}, "sucesso": True,
                    "mensagem": "Produto criado"}), 201


@api.put("/produtos/<int:id>")
def update_product(id):
    controllers.update_product(id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"})


@api.delete("/produtos/<int:id>")
def delete_product(id):
    controllers.delete_product(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"})


@api.get("/usuarios")
def list_users():
    return jsonify({"dados": controllers.list_users(), "sucesso": True})


@api.get("/usuarios/<int:id>")
def get_user(id):
    return jsonify({"dados": controllers.get_user(id), "sucesso": True})


@api.post("/usuarios")
def create_user():
    user_id = controllers.create_user(request.get_json(silent=True))
    return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201


@api.post("/login")
def login():
    return jsonify({"dados": controllers.login(request.get_json(silent=True)),
                    "sucesso": True, "mensagem": "Login OK"})


@api.post("/pedidos")
def create_order():
    result = controllers.create_order(request.get_json(silent=True))
    return jsonify({"dados": result, "sucesso": True,
                    "mensagem": "Pedido criado com sucesso"}), 201


@api.get("/pedidos")
def list_orders():
    return jsonify({"dados": controllers.list_orders(), "sucesso": True})


@api.get("/pedidos/usuario/<int:usuario_id>")
def list_user_orders(usuario_id):
    return jsonify({"dados": controllers.list_orders(usuario_id), "sucesso": True})


@api.put("/pedidos/<int:pedido_id>/status")
def update_order_status(pedido_id):
    controllers.update_order_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"})


@api.get("/relatorios/vendas")
def sales_report():
    return jsonify({"dados": controllers.sales_report(), "sucesso": True})


@api.get("/health")
def health():
    return jsonify(controllers.health())

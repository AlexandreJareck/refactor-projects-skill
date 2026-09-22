"""HTTP contracts and persistence behavior on isolated SQLite files."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import create_app
from database import get_db
import models


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = str(Path(self.folder.name) / "loja.db")
        self.app = create_app({"TESTING": True, "DATABASE": self.path})
        self.client = self.app.test_client()

    def call(self, method, path, body=None, status=200):
        response = self.client.open(path, method=method, json=body)
        self.assertEqual(response.status_code, status, (method, path, response.get_json()))
        return response.get_json()

    def make_user(self):
        body = self.call("POST", "/usuarios", {
            "nome": "Cliente", "email": "cliente@example.com", "senha": "segredo seguro"
        }, 201)
        return body["dados"]["id"]

    def test_boot_and_every_public_endpoint(self):
        with self.app.app_context():
            self.assertEqual(get_db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0], 10)
        self.assertIn("endpoints", self.call("GET", "/"))
        health = self.call("GET", "/health")
        self.assertEqual(health["status"], "ok")
        self.assertNotIn("secret_key", health)
        self.assertNotIn("db_path", health)
        self.assertEqual(len(self.call("GET", "/produtos")["dados"]), 10)
        self.assertEqual(self.call("GET", "/produtos/1")["dados"]["id"], 1)
        self.assertEqual(self.call("GET", "/produtos/busca?q=Mouse")["total"], 1)
        product_id = self.call("POST", "/produtos", {
            "nome": "Produto 'Teste", "preco": 10, "estoque": 3
        }, 201)["dados"]["id"]
        self.call("PUT", f"/produtos/{product_id}", {
            "nome": "Produto atualizado", "preco": 12, "estoque": 3
        })
        self.assertEqual(self.call("GET", f"/produtos/{product_id}")["dados"]["preco"], 12)
        self.call("DELETE", f"/produtos/{product_id}")
        self.call("GET", f"/produtos/{product_id}", status=404)

        user_id = self.make_user()
        users = self.call("GET", "/usuarios")["dados"]
        self.assertEqual(len(users), 1)
        self.assertNotIn("senha", users[0])
        self.assertNotIn("senha", self.call("GET", f"/usuarios/{user_id}")["dados"])
        self.assertEqual(self.call("POST", "/login", {
            "email": "cliente@example.com", "senha": "segredo seguro"
        })["dados"]["id"], user_id)
        with closing(sqlite3.connect(self.path)) as db:
            stored = db.execute("SELECT senha FROM usuarios WHERE id = ?", (user_id,)).fetchone()[0]
        self.assertNotEqual(stored, "segredo seguro")
        self.assertTrue(stored.startswith(("scrypt:", "pbkdf2:")))

        order = self.call("POST", "/pedidos", {
            "usuario_id": user_id, "itens": [{"produto_id": 1, "quantidade": 1}]
        }, 201)["dados"]
        self.assertGreater(order["total"], 0)
        self.assertEqual(len(self.call("GET", "/pedidos")["dados"]), 1)
        self.assertEqual(len(self.call("GET", f"/pedidos/usuario/{user_id}")["dados"]), 1)
        self.call("PUT", f"/pedidos/{order['pedido_id']}/status", {"status": "aprovado"})
        self.assertEqual(self.call("GET", "/relatorios/vendas")["dados"]["pedidos_aprovados"], 1)

    def test_failure_cases_and_removed_admin_routes(self):
        self.call("GET", "/produtos/99999", status=404)
        self.call("GET", "/produtos/busca?preco_min=abc", status=400)
        self.call("POST", "/produtos", {"nome": "A"}, 400)
        self.call("PUT", "/produtos/99999", {}, 404)
        self.call("PUT", "/produtos/1", {
            "nome": "Ok", "preco": 1, "estoque": 1, "categoria": "inválida"
        }, 400)
        self.call("DELETE", "/produtos/99999", status=404)
        self.call("GET", "/usuarios/99999", status=404)
        self.call("POST", "/usuarios", {}, 400)
        self.call("POST", "/login", {"email": "x", "senha": "x"}, 401)
        self.call("POST", "/pedidos", {"usuario_id": 1, "itens": []}, 400)
        user_id = self.make_user()
        original_stock = self.call("GET", "/produtos/1")["dados"]["estoque"]
        self.call("POST", "/pedidos", {"usuario_id": user_id,
            "itens": [{"produto_id": 1, "quantidade": -1}]}, 400)
        self.assertEqual(self.call("GET", "/produtos/1")["dados"]["estoque"], original_stock)
        self.call("PUT", "/pedidos/99999/status", {"status": "aprovado"}, 404)
        self.call("PUT", "/pedidos/99999/status", {"status": "inválido"}, 400)
        self.assertEqual(self.call("GET", "/relatorios/vendas")["dados"]["total_pedidos"], 0)
        self.call("POST", "/admin/query", {"sql": "SELECT 1"}, 404)
        self.call("POST", "/admin/reset-db", status=404)
        self.call("GET", "/health")

    def test_sql_injection_is_data_and_failed_write_rolls_back(self):
        self.make_user()
        self.call("POST", "/login", {
            "email": "' OR 1=1 --", "senha": "x"
        }, 401)
        self.call("GET", "/produtos/busca?q=%27%20OR%201%3D1%20--")
        with self.app.app_context():
            db = get_db()
            before = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
            stock = db.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()[0]
            with self.assertRaises(ValueError):
                models.create_order(1, [{"produto_id": 1, "quantidade": stock + 1,
                                         "preco_unitario": 1}], 1)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0], before)
            self.assertEqual(db.execute("SELECT estoque FROM produtos WHERE id = 1").fetchone()[0], stock)

    def test_order_listing_uses_one_query(self):
        user_id = self.make_user()
        for _ in range(3):
            self.call("POST", "/pedidos", {"usuario_id": user_id,
                "itens": [{"produto_id": 1, "quantidade": 1}]}, 201)
        with self.app.app_context():
            db = get_db()
            statements = []
            db.set_trace_callback(statements.append)
            self.assertEqual(len(models.list_orders()), 3)
            db.set_trace_callback(None)
        selects = [sql for sql in statements if sql.lstrip().upper().startswith("SELECT")]
        self.assertEqual(len(selects), 1)

    def test_legacy_password_migrates_once(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT, email TEXT, senha TEXT, tipo TEXT, criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            db.execute("INSERT INTO usuarios (nome,email,senha,tipo) VALUES (?,?,?,?)",
                       ("Antigo", "antigo@example.com", "senha antiga", "cliente"))
            db.commit()
        self.call("POST", "/login", {"email": "antigo@example.com", "senha": "senha antiga"})
        with closing(sqlite3.connect(self.path)) as db:
            stored = db.execute("SELECT senha FROM usuarios WHERE id = 1").fetchone()[0]
            self.assertNotEqual(stored, "senha antiga")
        self.call("POST", "/login", {"email": "antigo@example.com", "senha": "senha antiga"})

    def test_database_failure_is_sanitized(self):
        broken = create_app({"TESTING": True,
                             "DATABASE": str(Path(self.folder.name) / "missing" / "loja.db")})
        client = broken.test_client()
        for path in ("/produtos", "/usuarios", "/pedidos",
                     "/pedidos/usuario/1", "/relatorios/vendas", "/health"):
            response = client.get(path)
            self.assertEqual(response.status_code, 500, path)
            self.assertEqual(response.get_json(), {"erro": "Erro interno"})


if __name__ == "__main__":
    unittest.main()

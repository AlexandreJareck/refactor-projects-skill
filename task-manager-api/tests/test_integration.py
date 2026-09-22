import hashlib
import unittest
from threading import Thread
from unittest.mock import patch

import requests
from sqlalchemy import event
from werkzeug.serving import make_server

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User


class TaskManagerIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "PROPAGATE_EXCEPTIONS": False,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "SECRET_KEY": "test-only-secret",
            }
        )
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

        self.legacy_user = User(
            name="Legacy User",
            email="legacy@example.com",
            role="admin",
            password=hashlib.md5(b"1234").hexdigest(),
        )
        self.modern_user = User(
            name="Modern User", email="modern@example.com", role="user"
        )
        self.modern_user.set_password("safe-password")
        self.category = Category(
            name="Backend", description="Backend tasks", color="#123456"
        )
        db.session.add_all([self.legacy_user, self.modern_user, self.category])
        db.session.flush()
        self.task = Task(
            title="Existing task",
            description="Fixture",
            status="pending",
            priority=2,
            user_id=self.legacy_user.id,
            category_id=self.category.id,
        )
        db.session.add(self.task)
        db.session.commit()
        self.user_id = self.legacy_user.id
        self.task_id = self.task.id
        self.category_id = self.category.id
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def assert_no_password_key(self, value):
        if isinstance(value, dict):
            self.assertNotIn("password", value)
            for child in value.values():
                self.assert_no_password_key(child)
        elif isinstance(value, list):
            for child in value:
                self.assert_no_password_key(child)

    def test_application_boots_with_exact_original_route_map(self):
        rules = {
            (method, rule.rule)
            for rule in self.app.url_map.iter_rules()
            if rule.endpoint != "static"
            for method in rule.methods - {"HEAD", "OPTIONS"}
        }
        self.assertEqual(22, len(rules))

    def test_real_http_server_boots_and_answers_health(self):
        server = make_server("127.0.0.1", 0, self.app)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            response = requests.get(
                f"http://127.0.0.1:{server.server_port}/health", timeout=5
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual("ok", response.json()["status"])
        finally:
            server.shutdown()
            thread.join(timeout=5)

    def test_all_22_original_endpoints_success(self):
        responses = []
        responses.append(self.client.get("/"))
        responses.append(self.client.get("/health"))
        responses.append(self.client.get("/users"))
        responses.append(
            self.client.post(
                "/users",
                json={
                    "name": "Created User",
                    "email": "created@example.com",
                    "password": "pass1234",
                },
            )
        )
        created_user_id = responses[-1].get_json()["id"]
        responses.append(self.client.get(f"/users/{self.user_id}"))
        responses.append(
            self.client.put(f"/users/{created_user_id}", json={"name": "Updated"})
        )
        responses.append(self.client.delete(f"/users/{created_user_id}"))
        responses.append(self.client.get(f"/users/{self.user_id}/tasks"))
        responses.append(
            self.client.post(
                "/login", json={"email": "legacy@example.com", "password": "1234"}
            )
        )
        responses.append(self.client.get("/tasks"))
        responses.append(
            self.client.post(
                "/tasks",
                json={
                    "title": "Created task",
                    "user_id": self.user_id,
                    "category_id": self.category_id,
                },
            )
        )
        created_task_id = responses[-1].get_json()["id"]
        responses.append(self.client.get(f"/tasks/{self.task_id}"))
        responses.append(
            self.client.put(f"/tasks/{created_task_id}", json={"status": "done"})
        )
        responses.append(self.client.delete(f"/tasks/{created_task_id}"))
        responses.append(self.client.get("/tasks/search?q=Existing&priority=2"))
        responses.append(self.client.get("/tasks/stats"))
        responses.append(self.client.get("/reports/summary"))
        responses.append(self.client.get(f"/reports/user/{self.user_id}"))
        responses.append(self.client.get("/categories"))
        responses.append(
            self.client.post(
                "/categories", json={"name": "Created category", "color": "#abcdef"}
            )
        )
        created_category_id = responses[-1].get_json()["id"]
        responses.append(
            self.client.put(
                f"/categories/{created_category_id}", json={"name": "Updated category"}
            )
        )
        responses.append(self.client.delete(f"/categories/{created_category_id}"))

        self.assertEqual(22, len(responses))
        self.assertEqual(
            [200, 200, 200, 201, 200, 200, 200, 200, 200, 200, 201,
             200, 200, 200, 200, 200, 200, 200, 200, 201, 200, 200],
            [response.status_code for response in responses],
        )
        for response in responses:
            self.assert_no_password_key(response.get_json())

    def test_all_22_original_endpoints_have_representative_error(self):
        responses = [self.client.post("/"), self.client.post("/health")]
        with patch("routes.user_routes.user_controller.list_users", side_effect=RuntimeError):
            responses.append(self.client.get("/users"))
        responses.append(self.client.post("/users", json={}))
        responses.append(self.client.get("/users/999"))
        responses.append(self.client.put("/users/999", json={"name": "Missing"}))
        responses.append(self.client.delete("/users/999"))
        responses.append(self.client.get("/users/999/tasks"))
        responses.append(
            self.client.post(
                "/login", json={"email": "legacy@example.com", "password": "wrong"}
            )
        )
        with patch("routes.task_routes.task_controller.list_tasks", side_effect=RuntimeError):
            responses.append(self.client.get("/tasks"))
        responses.append(self.client.post("/tasks", json={}))
        responses.append(self.client.get("/tasks/999"))
        responses.append(self.client.put("/tasks/999", json={"title": "Missing"}))
        responses.append(self.client.delete("/tasks/999"))
        responses.append(self.client.get("/tasks/search?priority=not-a-number"))
        with patch("routes.task_routes.task_controller.task_stats", side_effect=RuntimeError):
            responses.append(self.client.get("/tasks/stats"))
        with patch("routes.report_routes.report_controller.summary_report", side_effect=RuntimeError):
            responses.append(self.client.get("/reports/summary"))
        responses.append(self.client.get("/reports/user/999"))
        with patch("routes.report_routes.category_controller.list_categories", side_effect=RuntimeError):
            responses.append(self.client.get("/categories"))
        responses.append(self.client.post("/categories", json={}))
        responses.append(self.client.put("/categories/999", json={"name": "Missing"}))
        responses.append(self.client.delete("/categories/999"))

        self.assertEqual(22, len(responses))
        self.assertTrue(all(response.status_code >= 400 for response in responses))
        self.assertEqual(500, responses[2].status_code)
        self.assertEqual({"error": "Erro interno"}, responses[2].get_json())

    def test_legacy_md5_is_upgraded_after_successful_login(self):
        response = self.client.post(
            "/login", json={"email": "legacy@example.com", "password": "1234"}
        )
        self.assertEqual(200, response.status_code)
        self.assert_no_password_key(response.get_json())
        db.session.expire_all()
        user = db.session.get(User, self.user_id)
        self.assertNotEqual(hashlib.md5(b"1234").hexdigest(), user.password)
        self.assertTrue(user.check_password("1234"))

    def test_query_counts_are_bounded_for_former_n_plus_one_endpoints(self):
        for index in range(8):
            user = User(name=f"User {index}", email=f"user{index}@example.com")
            user.set_password("password")
            category = Category(name=f"Category {index}")
            db.session.add_all([user, category])
            db.session.flush()
            db.session.add(
                Task(
                    title=f"Task {index}",
                    user_id=user.id,
                    category_id=category.id,
                )
            )
        db.session.commit()
        db.session.remove()

        engine = db.engine
        statements = []

        def record_query(*args):
            statements.append(args[2])

        event.listen(engine, "before_cursor_execute", record_query)
        try:
            for path, maximum in (
                ("/tasks", 1),
                ("/users", 1),
                ("/categories", 1),
                ("/reports/summary", 3),
            ):
                statements.clear()
                response = self.client.get(path)
                self.assertEqual(200, response.status_code, path)
                self.assertLessEqual(len(statements), maximum, path)
        finally:
            event.remove(engine, "before_cursor_execute", record_query)


if __name__ == "__main__":
    unittest.main()

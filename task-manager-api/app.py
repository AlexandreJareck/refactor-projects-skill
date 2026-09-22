from flask import Flask
from flask_cors import CORS

from config import Config
from database import db
from errors import register_error_handlers
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from utils.datetime_utils import utc_now


def create_app(config_overrides=None):
    application = Flask(__name__)
    application.config.from_object(Config)
    if config_overrides:
        application.config.update(config_overrides)

    CORS(application)
    db.init_app(application)
    application.register_blueprint(task_bp)
    application.register_blueprint(user_bp)
    application.register_blueprint(report_bp)
    register_error_handlers(application)

    @application.get("/health")
    def health():
        return {"status": "ok", "timestamp": str(utc_now())}

    @application.get("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    return application


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config["DEBUG"], host="0.0.0.0", port=5000)

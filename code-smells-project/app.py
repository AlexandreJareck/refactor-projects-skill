"""Application composition and centralized error mapping."""

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from config import load_config, server_config
from database import close_db, get_db
from errors import APIError
from views import api


def create_app(config=None):
    application = Flask(__name__)
    application.config.update(load_config())
    if config:
        application.config.update(config)
    CORS(application)
    application.register_blueprint(api)
    application.teardown_appcontext(close_db)

    @application.errorhandler(APIError)
    def expected_error(error):
        body = {"erro": error.message}
        if error.success_field:
            body["sucesso"] = False
        return jsonify(body), error.status

    @application.errorhandler(Exception)
    def unexpected_error(error):
        if isinstance(error, HTTPException):
            return jsonify({"erro": error.description}), error.code
        application.logger.exception("Falha ao processar requisição")
        return jsonify({"erro": "Erro interno"}), 500

    return application


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        get_db()
    app.run(**server_config())

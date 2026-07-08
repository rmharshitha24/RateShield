from flask import Flask

from app.config import Config
from app.database.session import db
from app.middleware.rate_limiter import register_rate_limiter
from app.routes.health import health_bp
from app.routes.logs import logs_bp
from app.routes.protected import protected_bp
from app.routes.stats import stats_bp
from app.routes.users import users_bp
from app.utils.errors import register_error_handlers
from app.utils.logging import configure_logging


def create_app(config_class: type[Config] = Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    configure_logging(app.config["LOG_LEVEL"])
    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_error_handlers(app)
    register_rate_limiter(app)

    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(protected_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(stats_bp)

    return app

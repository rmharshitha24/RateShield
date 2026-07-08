import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.config import Config
from app.database.session import db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    LOG_LEVEL = "CRITICAL"
    DEFAULT_RATE_LIMIT_ALGORITHM = "token_bucket"
    DEFAULT_MAX_REQUESTS = 2
    DEFAULT_TIME_WINDOW = 60
    DEFAULT_REFILL_RATE = 1
    DEFAULT_BUCKET_CAPACITY = 2


@pytest.fixture()
def app():
    test_app = create_app(TestConfig)
    yield test_app
    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()

import pytest
from app import create_app
from app.extensions import db as _db

@pytest.fixture(scope='session')
def test_app():
    app = create_app('testing')
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def test_client(test_app):
    return test_app.test_client()

@pytest.fixture(scope='function')
def test_db(test_app):
    _db.create_all()
    yield _db
    _db.session.remove()
    _db.drop_all()

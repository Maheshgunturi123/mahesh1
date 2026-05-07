import pytest
from app.models import User


@pytest.fixture
def client(test_app, test_db):
    """Function-scoped client with fresh app context (fresh g) per test."""
    with test_app.app_context():
        yield test_app.test_client()


def test_register_success(client):
    response = client.post('/auth/register', data={
        'email': 'test@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Account created. Welcome to GymTrack!' in response.data
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.password_hash != 'securepass123'
    assert user.is_admin is False
    assert user.created_at is not None


def test_register_duplicate_email(test_app, test_db, client):
    # Create the existing user directly (no login side-effect)
    existing = User(email='dup@example.com')
    existing.set_password('securepass123')
    test_db.session.add(existing)
    test_db.session.commit()
    # Fresh unauthenticated client tries to register with same email
    response = client.post('/auth/register', data={
        'email': 'dup@example.com',
        'password': 'anotherpass123',
        'confirm_password': 'anotherpass123',
    })
    assert b'An account with this email already exists.' in response.data
    assert User.query.filter_by(email='dup@example.com').count() == 1


def test_register_short_password(client):
    response = client.post('/auth/register', data={
        'email': 'short@example.com',
        'password': 'short',
        'confirm_password': 'short',
    })
    assert response.status_code == 200
    assert User.query.filter_by(email='short@example.com').first() is None


def test_register_invalid_email(client):
    response = client.post('/auth/register', data={
        'email': 'not-an-email',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    })
    assert response.status_code == 200
    assert User.query.filter_by(email='not-an-email').first() is None


def test_register_password_not_plaintext(client):
    client.post('/auth/register', data={
        'email': 'hash@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    })
    user = User.query.filter_by(email='hash@example.com').first()
    assert user is not None
    assert user.password_hash != 'securepass123'


def test_register_is_admin_defaults_false(client):
    client.post('/auth/register', data={
        'email': 'admin@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    })
    user = User.query.filter_by(email='admin@example.com').first()
    assert user is not None
    assert user.is_admin is False


def test_register_created_at_set(client):
    from datetime import datetime
    client.post('/auth/register', data={
        'email': 'timestamp@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123',
    })
    user = User.query.filter_by(email='timestamp@example.com').first()
    assert user is not None
    assert isinstance(user.created_at, datetime)


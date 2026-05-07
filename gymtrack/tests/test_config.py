import pytest
from app import create_app
from config import DevelopmentConfig, TestingConfig

def test_app_creates_successfully(test_app):
    assert test_app is not None

def test_development_config_sets_debug():
    app = create_app('development')
    assert app.config['DEBUG'] is True

def test_testing_config_uses_in_memory_sqlite(test_app):
    assert test_app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'

def test_testing_config_disables_csrf(test_app):
    assert test_app.config['WTF_CSRF_ENABLED'] is False

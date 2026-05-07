from flask import Blueprint
exercises_bp = Blueprint('exercises', __name__, url_prefix='/exercises')
from app.blueprints.exercises import routes  # noqa: F401, E402

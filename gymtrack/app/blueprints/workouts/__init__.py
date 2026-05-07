from flask import Blueprint
workouts_bp = Blueprint('workouts', __name__, url_prefix='/workouts')
from app.blueprints.workouts import routes  # noqa: F401, E402

from flask import Blueprint
progress_bp = Blueprint('progress', __name__, url_prefix='/progress')
from app.blueprints.progress import routes  # noqa: F401, E402

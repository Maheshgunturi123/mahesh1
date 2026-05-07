from flask import render_template
from app.blueprints.progress import progress_bp

@progress_bp.route('/')
def index():
    return render_template('base.html')

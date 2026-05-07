from flask import render_template
from app.blueprints.workouts import workouts_bp

@workouts_bp.route('/')
def index():
    return render_template('base.html')

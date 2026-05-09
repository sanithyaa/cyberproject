"""
Public routes: home, about.
"""
from flask import Blueprint, render_template
from models.election import Election
from models.candidate import Candidate

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    election   = Election.query.filter_by(is_active=True).first()
    candidates = Candidate.query.all()
    return render_template('index.html', election=election, candidates=candidates)


@public_bp.route('/about')
def about():
    return render_template('about.html')

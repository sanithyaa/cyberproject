"""
Voter routes: dashboard, vote page, vote submission, results.
Security:
  - login_required + voter_required on all routes
  - Duplicate vote prevention (DB unique constraint + has_voted flag)
  - CSRF on vote form
  - Parameterised ORM queries
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify)
from flask_login import login_required, current_user
from extensions import db
from models.candidate import Candidate
from models.vote import Vote
from models.election import Election
from models.audit_log import AuditLog
from security.decorators import voter_required
from utils.audit import log_action
from utils.mail_helper import send_vote_confirmation

voter_bp = Blueprint('voter', __name__)


@voter_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    election  = Election.query.filter_by(is_active=True).first()
    candidates = Candidate.query.all()
    return render_template('dashboard.html', election=election, candidates=candidates)


@voter_bp.route('/vote', methods=['GET', 'POST'])
@login_required
@voter_required
def vote():
    election = Election.query.filter_by(is_active=True).first()
    if not election:
        flash('No active election at the moment.', 'warning')
        return redirect(url_for('voter.dashboard'))

    if current_user.has_voted:
        flash('You have already cast your vote.', 'warning')
        return redirect(url_for('voter.results'))

    candidates = Candidate.query.all()

    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id', type=int)

        # Validate candidate exists
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            flash('Invalid candidate selection.', 'danger')
            return render_template('vote.html', candidates=candidates, election=election)

        # Double-check duplicate vote at DB level
        existing = Vote.query.filter_by(voter_id=current_user.id).first()
        if existing or current_user.has_voted:
            flash('Duplicate vote detected. Your vote was already recorded.', 'danger')
            return redirect(url_for('voter.results'))

        # Record vote
        vote_record = Vote(voter_id=current_user.id, candidate_id=candidate_id)
        current_user.has_voted = True
        db.session.add(vote_record)
        db.session.commit()

        log_action('VOTE_CAST', user_id=current_user.id,
                   detail=f'Voted for candidate_id={candidate_id}')

        # Optional email receipt
        send_vote_confirmation(current_user.email, candidate.name)

        flash(f'Your vote for {candidate.name} has been recorded!', 'success')
        return redirect(url_for('voter.vote_confirmation', candidate_id=candidate_id))

    return render_template('vote.html', candidates=candidates, election=election)


@voter_bp.route('/vote/confirmation/<int:candidate_id>')
@login_required
@voter_required
def vote_confirmation(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    return render_template('vote_confirmation.html', candidate=candidate)


@voter_bp.route('/results')
@login_required
def results():
    election   = Election.query.filter_by(is_active=True).first()
    candidates = Candidate.query.all()
    total_votes = Vote.query.count()

    results_data = []
    for c in candidates:
        pct = round((c.vote_count / total_votes * 100), 1) if total_votes else 0
        results_data.append({
            'id':         c.id,
            'name':       c.name,
            'party':      c.party,
            'photo':      c.photo,
            'votes':      c.vote_count,
            'percentage': pct,
        })

    results_data.sort(key=lambda x: x['votes'], reverse=True)
    winner = results_data[0] if results_data and total_votes > 0 else None

    return render_template('results.html',
                           results=results_data,
                           total_votes=total_votes,
                           winner=winner,
                           election=election)


@voter_bp.route('/api/results')
@login_required
def api_results():
    """JSON endpoint for live chart updates."""
    candidates  = Candidate.query.all()
    total_votes = Vote.query.count()
    data = [
        {
            'name':  c.name,
            'party': c.party,
            'votes': c.vote_count,
            'pct':   round(c.vote_count / total_votes * 100, 1) if total_votes else 0,
        }
        for c in candidates
    ]
    return jsonify({'candidates': data, 'total': total_votes})

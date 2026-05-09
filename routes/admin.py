"""
Admin routes: dashboard, candidate management, election control, user management.
Security:
  - admin_required on every route
  - CSRF on all forms
  - Parameterised ORM queries
  - Secure file upload (extension whitelist + UUID rename)
  - Audit logging
"""
import os, uuid
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.candidate import Candidate
from models.vote import Vote
from models.election import Election
from models.audit_log import AuditLog
from security.decorators import admin_required
from security.validators import sanitize_input, allowed_file
from utils.audit import log_action

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Dashboard ──────────────────────────────────────────────────────────────────
@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users    = User.query.filter_by(role='voter').count()
    total_votes    = Vote.query.count()
    total_candidates = Candidate.query.count()
    election       = Election.query.filter_by(is_active=True).first()
    recent_logs    = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(10).all()
    candidates     = Candidate.query.all()
    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_votes=total_votes,
                           total_candidates=total_candidates,
                           election=election,
                           recent_logs=recent_logs,
                           candidates=candidates)


# ── Candidate Management ───────────────────────────────────────────────────────
@admin_bp.route('/candidates')
@login_required
@admin_required
def candidates():
    all_candidates = Candidate.query.all()
    return render_template('admin/candidates.html', candidates=all_candidates)


@admin_bp.route('/candidates/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_candidate():
    if request.method == 'POST':
        name  = sanitize_input(request.form.get('name', ''))
        party = sanitize_input(request.form.get('party', ''))
        bio   = sanitize_input(request.form.get('bio', ''))

        if not name or not party:
            flash('Name and party are required.', 'danger')
            return render_template('admin/add_candidate.html')

        photo_filename = 'default_candidate.png'
        file = request.files.get('photo')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Invalid file type. Allowed: png, jpg, jpeg, gif, webp', 'danger')
                return render_template('admin/add_candidate.html')
            ext = file.filename.rsplit('.', 1)[1].lower()
            # Rename to UUID to prevent path traversal / overwrite attacks
            photo_filename = f'{uuid.uuid4().hex}.{ext}'
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
            file.save(upload_path)

        candidate = Candidate(name=name, party=party, bio=bio, photo=photo_filename)
        db.session.add(candidate)
        db.session.commit()
        log_action('ADD_CANDIDATE', user_id=current_user.id, detail=f'Added: {name}')
        flash(f'Candidate "{name}" added successfully.', 'success')
        return redirect(url_for('admin.candidates'))

    return render_template('admin/add_candidate.html')


@admin_bp.route('/candidates/edit/<int:cid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_candidate(cid):
    candidate = Candidate.query.get_or_404(cid)

    if request.method == 'POST':
        candidate.name  = sanitize_input(request.form.get('name', candidate.name))
        candidate.party = sanitize_input(request.form.get('party', candidate.party))
        candidate.bio   = sanitize_input(request.form.get('bio', candidate.bio or ''))

        file = request.files.get('photo')
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Invalid file type.', 'danger')
                return render_template('admin/edit_candidate.html', candidate=candidate)
            ext = file.filename.rsplit('.', 1)[1].lower()
            photo_filename = f'{uuid.uuid4().hex}.{ext}'
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_filename)
            file.save(upload_path)
            candidate.photo = photo_filename

        db.session.commit()
        log_action('EDIT_CANDIDATE', user_id=current_user.id, detail=f'Edited: {candidate.name}')
        flash('Candidate updated.', 'success')
        return redirect(url_for('admin.candidates'))

    return render_template('admin/edit_candidate.html', candidate=candidate)


@admin_bp.route('/candidates/delete/<int:cid>', methods=['POST'])
@login_required
@admin_required
def delete_candidate(cid):
    candidate = Candidate.query.get_or_404(cid)
    name = candidate.name
    db.session.delete(candidate)
    db.session.commit()
    log_action('DELETE_CANDIDATE', user_id=current_user.id, detail=f'Deleted: {name}')
    flash(f'Candidate "{name}" deleted.', 'success')
    return redirect(url_for('admin.candidates'))


# ── Election Control ───────────────────────────────────────────────────────────
@admin_bp.route('/election', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_election():
    election = Election.query.first()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            title = sanitize_input(request.form.get('title', ''))
            desc  = sanitize_input(request.form.get('description', ''))
            if not title:
                flash('Election title is required.', 'danger')
                return render_template('admin/election.html', election=election)
            if election:
                flash('An election already exists. Delete it first.', 'warning')
            else:
                election = Election(title=title, description=desc)
                db.session.add(election)
                db.session.commit()
                log_action('CREATE_ELECTION', user_id=current_user.id, detail=title)
                flash('Election created.', 'success')

        elif action == 'start' and election:
            from datetime import datetime
            election.is_active  = True
            election.start_time = datetime.utcnow()
            db.session.commit()
            log_action('START_ELECTION', user_id=current_user.id)
            flash('Election started.', 'success')

        elif action == 'stop' and election:
            from datetime import datetime
            election.is_active = False
            election.end_time  = datetime.utcnow()
            db.session.commit()
            log_action('STOP_ELECTION', user_id=current_user.id)
            flash('Election stopped.', 'success')

        elif action == 'delete' and election:
            db.session.delete(election)
            db.session.commit()
            election = None
            log_action('DELETE_ELECTION', user_id=current_user.id)
            flash('Election deleted.', 'success')

        return redirect(url_for('admin.manage_election'))

    return render_template('admin/election.html', election=election)


# ── User Management ────────────────────────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.filter_by(role='voter').all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/toggle/<int:uid>', methods=['POST'])
@login_required
@admin_required
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.is_admin:
        flash('Cannot deactivate an admin account.', 'danger')
        return redirect(url_for('admin.manage_users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    log_action(f'USER_{status.upper()}', user_id=current_user.id,
               detail=f'User {user.username} {status}')
    flash(f'User {user.username} {status}.', 'success')
    return redirect(url_for('admin.manage_users'))


@admin_bp.route('/users/reset-vote/<int:uid>', methods=['POST'])
@login_required
@admin_required
def reset_vote(uid):
    user = User.query.get_or_404(uid)
    Vote.query.filter_by(voter_id=uid).delete()
    user.has_voted = False
    db.session.commit()
    log_action('RESET_VOTE', user_id=current_user.id, detail=f'Reset vote for {user.username}')
    flash(f'Vote reset for {user.username}.', 'success')
    return redirect(url_for('admin.manage_users'))


# ── Audit Logs ─────────────────────────────────────────────────────────────────
@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    logs = (AuditLog.query
            .order_by(AuditLog.timestamp.desc())
            .paginate(page=page, per_page=25, error_out=False))
    return render_template('admin/audit_logs.html', logs=logs)


# ── Results ────────────────────────────────────────────────────────────────────
@admin_bp.route('/results')
@login_required
@admin_required
def results():
    candidates  = Candidate.query.all()
    total_votes = Vote.query.count()
    results_data = []
    for c in candidates:
        pct = round(c.vote_count / total_votes * 100, 1) if total_votes else 0
        results_data.append({
            'id': c.id, 'name': c.name, 'party': c.party,
            'photo': c.photo, 'votes': c.vote_count, 'percentage': pct,
        })
    results_data.sort(key=lambda x: x['votes'], reverse=True)
    winner = results_data[0] if results_data and total_votes > 0 else None
    return render_template('admin/results.html',
                           results=results_data,
                           total_votes=total_votes,
                           winner=winner)

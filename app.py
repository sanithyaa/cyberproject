"""
Application factory and entry point.
Run with:  python app.py
"""
import os
from flask import Flask, render_template
from config import config
from extensions import db, bcrypt, login_manager, csrf, mail, limiter


def create_app(config_name: str = 'default') -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # --- Template filters ---
    from datetime import datetime
    def timeago(dt):
        """Return a human-friendly relative time string for a datetime object."""
        if not dt:
            return '—'
        now = datetime.utcnow()
        diff = now - dt
        seconds = int(diff.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = hours // 24
        if seconds < 60:
            return f'{seconds} sec ago' if seconds > 0 else 'just now'
        if minutes < 60:
            return f'{minutes} min ago'
        if hours < 48:
            return f'{hours} hr ago' if hours == 1 else f'{hours} hrs ago'
        return dt.strftime('%Y-%m-%d')

    app.add_template_filter(timeago, name='timeago')

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Initialise extensions ──────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ── Register blueprints ────────────────────────────────────────────────────
    from routes.public import public_bp
    from routes.auth   import auth_bp
    from routes.voter  import voter_bp
    from routes.admin  import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(voter_bp)
    app.register_blueprint(admin_bp)

    # ── Security headers (applied to every response) ───────────────────────────
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options']  = 'nosniff'
        response.headers['X-Frame-Options']          = 'DENY'
        response.headers['X-XSS-Protection']         = '1; mode=block'
        response.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy']  = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'unsafe-inline'; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data:;"
        )
        return response

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Create tables + seed admin ─────────────────────────────────────────────
    with app.app_context():
        db.create_all()
        _seed_admin()
        # Run demo seeding only when explicitly allowed by config (default True)
        if app.config.get('SEED_DEMO', True):
            _seed_demo()

    return app


def _seed_admin():
    """Create a default admin account if none exists."""
    from models.user import User
    from utils.mail_helper import generate_otp_secret
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username    = 'admin',
            email       = 'admin@votingsystem.com',
            role        = 'admin',
            is_verified = True,
            otp_secret  = generate_otp_secret(),
        )
        admin.set_password('Admin@1234')   # change immediately after first login
        db.session.add(admin)
        db.session.commit()
        print('[SEED] Default admin created  →  username: admin  password: Admin@1234')


def _seed_demo():
    """Populate the database with realistic dummy data for development/demos.
    This will only add data when the target tables are empty to avoid duplication.
    """
    import random
    from datetime import datetime, timedelta
    from models.user import User
    from models.candidate import Candidate
    from models.election import Election
    from models.vote import Vote
    from models.audit_log import AuditLog

    now = datetime.utcnow()

    # --- Users ---
    user_count = User.query.count()
    if user_count < 10:
        print('[SEED] Creating demo users...')
        demo_users = []
        # Keep existing admin; create 12 total users (including any existing ones)
        target = 12
        start_idx = 1
        # find a starting index that doesn't conflict with existing usernames
        existing_usernames = {u.username for u in User.query.all()}
        i = 1
        while len(demo_users) + user_count < target:
            uname = f'user{i}'
            if uname in existing_usernames or uname == 'admin':
                i += 1
                continue
            u = User(username=uname, email=f'{uname}@example.com', role='voter', is_verified=True)
            u.set_password('Password123!')
            # randomize last_login within past 7 days
            u.last_login = now - timedelta(days=random.randint(0, 6), hours=random.randint(0,23))
            demo_users.append(u)
            existing_usernames.add(uname)
            i += 1

        # Add one extra admin user for demo if none exists besides default
        if not User.query.filter_by(role='admin').filter(User.username!='admin').first():
            admin_demo = User(username='manager', email='manager@example.com', role='admin', is_verified=True)
            admin_demo.set_password('Manager123!')
            admin_demo.last_login = now - timedelta(hours=2)
            demo_users.append(admin_demo)

        db.session.add_all(demo_users)
        db.session.commit()
        print(f'[SEED] Added {len(demo_users)} demo users')

    # --- Candidates ---
    cand_count = Candidate.query.count()
    if cand_count == 0:
        print('[SEED] Creating demo candidates...')
        candidates = [
            Candidate(name='Alice Johnson', party='Progressive Alliance', photo='default_candidate.png', bio='Focused on transparency.'),
            Candidate(name='Brian Chen', party='Unity Party', photo='default_candidate.png', bio='Community-first platform.'),
            Candidate(name='Carlos Rivera', party='Forward Movement', photo='default_candidate.png', bio='Innovation and jobs.'),
            Candidate(name='Diana Patel', party='Green Horizon', photo='default_candidate.png', bio='Sustainability and health.'),
        ]
        db.session.add_all(candidates)
        db.session.commit()
        print(f'[SEED] Added {len(candidates)} demo candidates')

    # --- Election ---
    elect_count = Election.query.count()
    if elect_count == 0:
        print('[SEED] Creating active demo election...')
        election = Election(
            title='General Election 2025',
            description='Demo election for showcasing the SecureVote admin UI.',
            is_active=True,
            start_time=now - timedelta(days=2),
            end_time=now + timedelta(days=7)
        )
        db.session.add(election)
        db.session.commit()
        print('[SEED] Demo election created')

    # --- Votes ---
    vote_count = Vote.query.count()
    if vote_count == 0:
        print('[SEED] Generating demo votes...')
        voters = User.query.filter_by(role='voter').all()
        candidates = Candidate.query.all()
        if voters and candidates:
            # Random subset of voters cast votes (not all)
            num_voters = len(voters)
            num_voted = max(1, int(num_voters * 0.65))  # ~65% voted
            voted_sample = random.sample(voters, k=num_voted)
            votes = []
            for v in voted_sample:
                choice = random.choice(candidates)
                # random timestamp within election window
                ts = now - timedelta(days=random.randint(0, 2), hours=random.randint(0,23), minutes=random.randint(0,59))
                vote = Vote(voter_id=v.id, candidate_id=choice.id, timestamp=ts)
                votes.append(vote)
                v.has_voted = True

            db.session.add_all(votes)
            db.session.commit()
            print(f'[SEED] Added {len(votes)} votes')

    # --- Audit Logs ---
    audit_count = AuditLog.query.count()
    if audit_count == 0:
        print('[SEED] Creating demo audit logs...')
        # Attempt to attach logs to an admin user if present
        admin = User.query.filter_by(role='admin').first()
        sample_voter = User.query.filter_by(role='voter').first()
        sample_candidate = Candidate.query.first()
        logs = []
        logs.append(AuditLog(user_id=admin.id if admin else None, action='Admin logged in', detail='Interactive demo login', ip_address='127.0.0.1', timestamp=now - timedelta(minutes=5)))
        logs.append(AuditLog(user_id=admin.id if admin else None, action='Election created', detail='General Election 2025', ip_address=None, timestamp=now - timedelta(days=2)))
        logs.append(AuditLog(user_id=admin.id if admin else None, action='Candidate added', detail=sample_candidate.name if sample_candidate else 'Alice Johnson', ip_address=None, timestamp=now - timedelta(days=1, hours=3)))
        logs.append(AuditLog(user_id=sample_voter.id if sample_voter else None, action='Vote cast', detail=f'Voted for {sample_candidate.name if sample_candidate else "—"}', ip_address='192.168.1.12', timestamp=now - timedelta(hours=1)))
        db.session.add_all(logs)
        db.session.commit()
        print(f'[SEED] Added {len(logs)} audit logs')

    print('[SEED] Demo data seeding complete')


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    flask_app = create_app(os.environ.get('FLASK_ENV', 'development'))
    flask_app.run(debug=True, host='0.0.0.0', port=5000)

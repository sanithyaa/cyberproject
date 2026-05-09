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


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    flask_app = create_app(os.environ.get('FLASK_ENV', 'development'))
    flask_app.run(debug=True, host='0.0.0.0', port=5000)

"""
Authentication routes: register, login, logout, OTP verification.

OTP flow:
  REGISTRATION → fill form → OTP sent to email → verify OTP → account created → login
  LOGIN        → credentials → OTP sent to email → verify OTP → logged in

Security measures:
  - bcrypt password hashing
  - CSRF protection (Flask-WTF)
  - Rate limiting on login (brute-force prevention)
  - Parameterised queries via SQLAlchemy ORM
  - Input validation before any DB write
  - Registration data held in session until OTP verified (no DB write on unverified email)
  - Audit logging for every auth event
"""
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, bcrypt, limiter
from models.user import User
from security.validators import (validate_username, validate_email,
                                  validate_password, sanitize_input)
from utils.audit import log_action
from utils.mail_helper import (generate_otp_secret, get_totp, send_otp_email)
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


# ── Registration – Step 1: collect details ─────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("20 per hour")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('voter.dashboard'))

    if request.method == 'POST':
        # Sanitise inputs (XSS prevention)
        username = sanitize_input(request.form.get('username', ''))
        email    = sanitize_input(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # ── Validate all fields ────────────────────────────────────────────────
        ok, msg = validate_username(username)
        if not ok:
            flash(msg, 'danger'); return render_template('register.html')

        ok, msg = validate_email(email)
        if not ok:
            flash(msg, 'danger'); return render_template('register.html')

        ok, msg = validate_password(password)
        if not ok:
            flash(msg, 'danger'); return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # ── Check uniqueness (parameterised ORM query) ─────────────────────────
        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        # ── Store pending registration in session (NOT in DB yet) ──────────────
        # The account is only created after the OTP is verified.
        otp_secret = generate_otp_secret()
        session['pending_registration'] = {
            'username':   username,
            'email':      email,
            'password_hash': bcrypt.generate_password_hash(password).decode('utf-8'),
            'otp_secret': otp_secret,
        }

        # ── Send OTP to the supplied email ─────────────────────────────────────
        otp_code = get_totp(otp_secret).now()
        send_otp_email(email, otp_code)   # silently fails if mail not configured

        # Demo mode: show OTP in flash so it works without email setup
        flash(f'[DEMO] Registration OTP for {email}: {otp_code}  (expires in 5 min)', 'info')
        log_action('REGISTER_OTP_SENT', detail=f'OTP sent to {email} for new registration')

        return redirect(url_for('auth.verify_register_otp'))

    return render_template('register.html')


# ── Registration – Step 2: verify OTP → create account ────────────────────────
@auth_bp.route('/verify-register-otp', methods=['GET', 'POST'])
def verify_register_otp():
    pending = session.get('pending_registration')
    if not pending:
        flash('Session expired. Please register again.', 'warning')
        return redirect(url_for('auth.register'))

    if request.method == 'GET':
        # Re-send OTP on page refresh so the timer stays fresh
        otp_code = get_totp(pending['otp_secret']).now()
        send_otp_email(pending['email'], otp_code)
        flash(f'[DEMO] Your registration OTP is: {otp_code}  (expires in 5 min)', 'info')

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        totp = get_totp(pending['otp_secret'])

        if totp.verify(entered_otp):
            # ── OTP correct → create the account now ──────────────────────────
            # Double-check uniqueness again (race condition guard)
            if (User.query.filter_by(username=pending['username']).first() or
                    User.query.filter_by(email=pending['email']).first()):
                session.pop('pending_registration', None)
                flash('Username or email was just taken. Please register again.', 'danger')
                return redirect(url_for('auth.register'))

            user = User(
                username      = pending['username'],
                email         = pending['email'],
                password_hash = pending['password_hash'],
                role          = 'voter',
                is_verified   = True,
                otp_secret    = pending['otp_secret'],
            )
            db.session.add(user)
            db.session.commit()

            session.pop('pending_registration', None)
            log_action('REGISTER_SUCCESS', user_id=user.id,
                       detail=f'Account created: {user.username}')
            flash('Email verified! Your account is ready. Please log in.', 'success')
            return redirect(url_for('auth.login'))

        else:
            log_action('REGISTER_OTP_FAILED', detail=f'Bad OTP for {pending["email"]}')
            flash('Invalid or expired OTP. Please try again.', 'danger')

    return render_template('verify_otp.html',
                           email=pending['email'],
                           purpose='registration')


# ── Login – Step 1: credentials ────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")   # brute-force protection
def login():
    if current_user.is_authenticated:
        return redirect(url_for('voter.dashboard'))

    if request.method == 'POST':
        username = sanitize_input(request.form.get('username', ''))
        password = request.form.get('password', '')

        # Parameterised ORM query – immune to SQL injection
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active:
            # Store user id in session for OTP step
            session['pre_auth_user_id'] = user.id
            log_action('LOGIN_ATTEMPT', user_id=user.id,
                       detail='Credentials verified, OTP pending')
            return redirect(url_for('auth.verify_login_otp'))
        else:
            log_action('LOGIN_FAILED', detail=f'Failed login for: {username}')
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')


# ── Login – Step 2: OTP ────────────────────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_login_otp():
    user_id = session.get('pre_auth_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'GET':
        otp_code = get_totp(user.otp_secret).now()
        send_otp_email(user.email, otp_code)
        flash(f'[DEMO] Your login OTP is: {otp_code}  (expires in 5 min)', 'info')

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        totp = get_totp(user.otp_secret)

        if totp.verify(entered_otp):
            session.pop('pre_auth_user_id', None)
            login_user(user, remember=False)
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_action('LOGIN_SUCCESS', user_id=user.id)
            flash(f'Welcome back, {user.username}!', 'success')
            if user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('voter.dashboard'))
        else:
            log_action('OTP_FAILED', user_id=user.id)
            flash('Invalid or expired OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', email=user.email, purpose='login')


# ── Logout ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    log_action('LOGOUT', user_id=current_user.id)
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

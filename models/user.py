from extensions import db, bcrypt, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """
    Stores registered voters and admins.
    Passwords are NEVER stored in plain text – only bcrypt hashes.
    """
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20),  nullable=False, default='voter')  # 'admin' | 'voter'
    has_voted     = db.Column(db.Boolean, default=False, nullable=False)
    is_active     = db.Column(db.Boolean, default=True,  nullable=False)
    is_verified   = db.Column(db.Boolean, default=False, nullable=False)
    otp_secret    = db.Column(db.String(32), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)

    # Relationship
    votes = db.relationship('Vote', backref='voter', lazy=True)

    # ── Password helpers ──────────────────────────────────────────────────────
    def set_password(self, plain_password: str):
        """Hash and store the password using bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(plain_password).decode('utf-8')

    def check_password(self, plain_password: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, plain_password)

    # ── Role helpers ──────────────────────────────────────────────────────────
    @property
    def is_admin(self) -> bool:
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

from extensions import db
from datetime import datetime


class AuditLog(db.Model):
    """
    Immutable audit trail – every security-relevant action is recorded here.
    Rows are INSERT-only; never updated or deleted.
    """
    __tablename__ = 'audit_logs'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action     = db.Column(db.String(100), nullable=False)
    detail     = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)   # supports IPv6
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref='audit_logs', lazy=True)

    def __repr__(self):
        return f'<AuditLog {self.action} by user={self.user_id} at {self.timestamp}>'

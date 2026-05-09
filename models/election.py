from extensions import db
from datetime import datetime


class Election(db.Model):
    """Tracks the current election state (only one active election at a time)."""
    __tablename__ = 'elections'

    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active   = db.Column(db.Boolean, default=False, nullable=False)
    start_time  = db.Column(db.DateTime, nullable=True)
    end_time    = db.Column(db.DateTime, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Election {self.title} active={self.is_active}>'

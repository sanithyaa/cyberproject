from extensions import db
from datetime import datetime


class Candidate(db.Model):
    """Represents a candidate in an election."""
    __tablename__ = 'candidates'

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    party      = db.Column(db.String(120), nullable=False)
    photo      = db.Column(db.String(256), nullable=True, default='default_candidate.png')
    bio        = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    votes = db.relationship('Vote', backref='candidate', lazy=True)

    @property
    def vote_count(self) -> int:
        return len(self.votes)

    def __repr__(self):
        return f'<Candidate {self.name} – {self.party}>'

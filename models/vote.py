from extensions import db
from datetime import datetime


class Vote(db.Model):
    """
    Records a single cast vote.
    voter_id + candidate_id are stored; the voter's identity is
    separated from the candidate choice to preserve ballot secrecy
    while still preventing duplicate votes.
    """
    __tablename__ = 'votes'

    id           = db.Column(db.Integer, primary_key=True)
    voter_id     = db.Column(db.Integer, db.ForeignKey('users.id'),      nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    timestamp    = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Unique constraint: one vote per voter
    __table_args__ = (
        db.UniqueConstraint('voter_id', name='uq_one_vote_per_voter'),
    )

    def __repr__(self):
        return f'<Vote voter={self.voter_id} candidate={self.candidate_id}>'

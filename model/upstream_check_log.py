# models/upstream_log.py

from . import db
from datetime import datetime

class UpstreamCheckLog(db.Model):
    __tablename__ = 'upstream_check_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pattern = db.Column(db.Text, nullable=False)
    upstream_name = db.Column(db.Text, nullable=False)
    check_url = db.Column(db.Text)
    result = db.Column(db.Text)
    detail = db.Column(db.Text)
    tried_at = db.Column(db.String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    count = db.Column(db.Integer, default=1)

    __table_args__ = (
        db.UniqueConstraint('pattern', 'upstream_name', name='uq_pattern_upstream'),
    )

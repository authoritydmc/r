# models/upstream_log.py

from . import db
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert # Keep this if you are using PostgreSQL

class UpstreamCheckLog(db.Model):
    __tablename__ = 'upstream_check_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pattern = db.Column(db.Text, nullable=False)
    upstream_name = db.Column(db.Text, nullable=False)
    check_url = db.Column(db.Text)
    result = db.Column(db.Text)
    detail = db.Column(db.Text)
    tried_at = db.Column(db.String, default=lambda: datetime.now(timezone.utc).isoformat(), nullable=False)
    count = db.Column(db.Integer, default=1)
    cached = db.Column(db.Boolean, default=False) # This is the boolean column

    __table_args__ = (
        db.UniqueConstraint('pattern', 'upstream_name', name='uq_pattern_upstream'),
    )

    @classmethod
    def upsert_log(cls, pattern: str, upstream_name: str, check_url: str,
                   result: str, detail: str, cached: bool):
        """
        Inserts a new upstream check log entry or updates an existing one
        if a conflict occurs on 'pattern' and 'upstream_name'.

        Updates all provided fields to their new values and increments the 'count'.
        """
        current_tried_at = datetime.now(timezone.utc).isoformat()

        # Define the values for the INSERT part of the UPSERT
        # These are the "excluded" values if a conflict occurs
        insert_values = {
            'pattern': pattern,
            'upstream_name': upstream_name,
            'check_url': check_url,
            'result': result,
            'detail': detail,
            'tried_at': current_tried_at,
            'count': 1,  # Initial count for a new insert
            'cached': cached # This is the boolean value
        }

        # Create the insert statement
        stmt = insert(cls).values(**insert_values)

        # Define what to do on conflict: update specific columns
        on_conflict_stmt = stmt.on_conflict_do_update(
            constraint='uq_pattern_upstream',
            set_=dict(
                check_url=stmt.excluded.check_url,
                result=stmt.excluded.result,
                detail=stmt.excluded.detail,
                tried_at=stmt.excluded.tried_at,
                cached=stmt.excluded.cached,
                # Increment the existing count from the current row value
                count=cls.count + 1
            )
        )

        db.session.execute(on_conflict_stmt)
        # Remember to call db.session.commit() in your calling function (e.g., in log_upstream_check)!
from . import db

class Redirect(db.Model):
    __tablename__ = 'redirects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.String, nullable=False)
    pattern = db.Column(db.String, nullable=False)
    target = db.Column(db.String, nullable=False)

    def __repr__(self):
        return f"<Redirect(id={self.id}, type='{self.type}', pattern='{self.pattern}', target='{self.target}')>"

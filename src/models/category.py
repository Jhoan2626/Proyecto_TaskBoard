from datetime import datetime, timezone
from src.models import db

def get_utc_now():
    return datetime.now(timezone.utc)

class Category(db.Model):
    __tablename__ = 'categories'
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='uq_category_user_name'),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=get_utc_now, nullable=False)

    user = db.relationship('User', back_populates='categories')
    tasks = db.relationship('Task', backref='category', lazy=True, passive_deletes=True)

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'


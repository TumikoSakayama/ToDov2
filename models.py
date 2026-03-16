from datetime import datetime
from sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    notes = db.relationship('Note', backref='category', lazy=True)

    def __repr__(self):
        return f'Category {self.name}'

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    priority = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime)
    is_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=True)
    subtasks = db.relationship('Note', backref=db.backref('parent', remote_side=[id]), lazy=True, cascade="all, delete-orphan")
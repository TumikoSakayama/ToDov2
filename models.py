from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Association table for the many-to-many relationship between Notes and Tags
note_tags = db.Table('note_tags',
    db.Column('note_id', db.Integer, db.ForeignKey('notes.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

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
    tags = db.relationship('Tag', secondary=note_tags, lazy='subquery',
                           backref=db.backref('notes', lazy=True))
    recurrence_rule = db.Column(db.String(200), nullable=True) # iCalendar RRULE format
    next_occurrence_date = db.Column(db.DateTime, nullable=True)
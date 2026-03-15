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
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
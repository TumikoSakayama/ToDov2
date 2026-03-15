from flask import Flask, render_template
from sqlalchemy import sql

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URL'] = 'sqlite:///todo.db'
db = sql(app)

class Note(db.Model):
    __tablename___ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    priority = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category_id'))
    category = db.relationship("Category", backref=db.backref('notes', lazy=True))
    deadline = db.Column(db.DateTime)

class Category(db.Model):
    __tablename___ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50, nullable=False, unique=True))
    notes = db.relationship('Note', backref='category', lazy=True)

    def __str__(self):
        return self.name
    

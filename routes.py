from flask import Blueprint, jsonify
from models import Note, Category

notes_blueprint = Blueprint('note', __name__)

@notes_blueprint.route('/api/notes', methods=['GET'])
def get_all_notes():
    notes = Note.query.all()

    return jsonify([{
        'id': n.id,
        'title': n.title,
        'priority': n.priority,
        'deadline': str(n.deadline) if n.deadline else None,
        'category': n.category.name if n.category else None
    }for n in notes])\

@notes_blueprint.route('/api/categories', methods['GET']) 
def get_all_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name
    } for c in categories])
from flask import Blueprint, jsonify, request
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

@notes_blueprint.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json()
    new_note = Note(
        title = data['title'],
        description = data['description'],
        priority = data['priority', 0],
        category_id = data['category_id']
    )
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note created successfully'}), 201

@notes_blueprint.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted'})
from flask import Blueprint, request, jsonify
from models import Note, Category

notes_blueprint = Blueprint('notes', __name__)

@notes_blueprint.route('api/notes', method=['GET'])
def get_all_notes():
    notes = Note.query.all()
    return jsonify([{'title': note.title, 'deadline': str(note.deadline)} for note in notes])

@notes_blueprint.route('api/categories', methods=['GET'])
def get_all_categories():
    categories = Category.query.all()
    return jsonify([{'id': cat.id, 'name':cat.name} for cat in categories])
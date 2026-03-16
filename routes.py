from flask import Blueprint, jsonify, request
from models import db, Note, Category
from datetime import datetime, timedelta
from sqlalchemy import extract

notes_blueprint = Blueprint('note', __name__)

@notes_blueprint.route('/api/notes', methods=['GET'])
def get_all_notes():
    query = Note.query

    # 1. Filtering by Category or Priority
    category_id = request.args.get('category_id')
    if category_id:
        query = query.filter(Note.category_id == category_id)

    priority = request.args.get('priority')
    if priority:
        query = query.filter(Note.priority == priority)

    # 2. Filter by Task added in a given day
    created_date = request.args.get('created_date') # Format YYYY-MM-DD
    if created_date:
        try:
            # Filter range for the specific day
            dt = datetime.strptime(created_date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(Note.created_at >= dt, Note.created_at < next_day)
        except ValueError:
            pass # Handle invalid date format gracefully

    # 3. Show task by week or month (Time filtering on Deadline)
    view = request.args.get('view')
    if view:
        today = datetime.now()
        if view == 'week':
            # Tasks due in the next 7 days or current week
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=7)
            query = query.filter(Note.deadline >= start_of_week, Note.deadline < end_of_week)
        elif view == 'month':
            # Tasks due this month
            query = query.filter(extract('month', Note.deadline) == today.month)
            query = query.filter(extract('year', Note.deadline) == today.year)

    # 4. Sorting
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    if hasattr(Note, sort_by):
        column = getattr(Note, sort_by)
        if order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    notes = query.all()

    return jsonify([{
        'id': n.id,
        'title': n.title,
        'description': n.description,
        'priority': n.priority,
        'is_done': n.is_done,
        'deadline': n.deadline.isoformat() if n.deadline else None,
        'created_at': n.created_at.isoformat() if n.created_at else None,
        'category': n.category.name if n.category else None,
        'category_id': n.category_id,
        'parent_id': n.parent_id,
        'subtasks': [sub.id for sub in n.subtasks]
    } for n in notes])

@notes_blueprint.route('/api/categories', methods=['GET']) 
def get_all_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name
    } for c in categories])

@notes_blueprint.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json
    
    deadline = None
    if data.get('deadline'):
        try:
            deadline = datetime.fromisoformat(data['deadline'])
        except ValueError:
            pass

    new_note = Note(
        title = data.get('title'),
        description = data.get('description'),
        priority = data.get('priority', 0),
        is_done = data.get('is_done', False),
        deadline = deadline,
        category_id = data.get('category_id'),
        parent_id = data.get('parent_id') # Handle subtasks
    )
    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note created successfully'}), 201

@notes_blueprint.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    note = Note.query.get_or_404(note_id)
    data = request.json

    note.title = data.get('title', note.title)
    note.description = data.get('description', note.description)
    note.priority = data.get('priority', note.priority)
    note.category_id = data.get('category_id', note.category_id)
    note.parent_id = data.get('parent_id', note.parent_id)
    
    if 'is_done' in data:
        note.is_done = data['is_done']
        if note.is_done:
            # Recursively mark all subtasks as done
            def mark_subtasks_done(task):
                for sub in task.subtasks:
                    sub.is_done = True
                    mark_subtasks_done(sub)
            mark_subtasks_done(note)

    if note.parent_id == note.id:
        return jsonify({'error': 'A task cannot be its own subtask'}), 400
    
    if 'deadline' in data:
        if data['deadline']:
            try:
                note.deadline = datetime.fromisoformat(data['deadline'])
            except ValueError:
                pass
        else:
            note.deadline = None

    db.session.commit()
    return jsonify({'message': 'Note updated successfully'})

@notes_blueprint.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note deleted'})
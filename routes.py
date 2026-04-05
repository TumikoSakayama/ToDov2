from flask import Blueprint, jsonify, request
from models import db, Note, Category, Tag
from datetime import datetime, timedelta
from sqlalchemy import extract
from dateutil.rrule import rrulestr

notes_blueprint = Blueprint('note', __name__)

# Helper for serialization to support nesting and tags
def serialize_note(note, nested=False):
    data = {
        'id': note.id,
        'title': note.title,
        'description': note.description,
        'priority': note.priority,
        'is_done': note.is_done,
        'deadline': note.deadline.isoformat() if note.deadline else None,
        'created_at': note.created_at.isoformat() if note.created_at else None,
        'category': note.category.name if note.category else None,
        'category_id': note.category_id,
        'parent_id': note.parent_id,
        'tags': [tag.name for tag in note.tags],
        'recurrence_rule': note.recurrence_rule,
        'next_occurrence_date': note.next_occurrence_date.isoformat() if note.next_occurrence_date else None
    }
    if nested:
        data['subtasks'] = [serialize_note(sub, nested=True) for sub in note.subtasks]
    else:
        data['subtasks'] = [sub.id for sub in note.subtasks]
    return data

@notes_blueprint.route('/')
def index():
    """A simple view to confirm the app is running and provide guidance."""
    return ("<h1>Todo App Backend is Running!</h1>"
            "<p>This is the backend server. Your API endpoints are available at:</p>"
            "<ul><li><a href='/api/notes'>/api/notes</a></li><li><a href='/api/categories'>/api/categories</a></li><li><a href='/api/tags'>/api/tags</a></li></ul>")

@notes_blueprint.route('/api/notes', methods=['GET'])
def get_all_notes():
    query = Note.query

    # 1. Filtering
    category_id = request.args.get('category_id')
    if category_id:
        query = query.filter(Note.category_id == category_id)

    priority = request.args.get('priority')
    if priority:
        query = query.filter(Note.priority == priority)

    tag_name = request.args.get('tag')
    if tag_name:
        query = query.join(Note.tags).filter(Tag.name == tag_name)


    created_date = request.args.get('created_date') # Format YYYY-MM-DD
    if created_date:
        try:
            # Filter range for the specific day
            dt = datetime.strptime(created_date, '%Y-%m-%d')
            next_day = dt + timedelta(days=1)
            query = query.filter(Note.created_at >= dt, Note.created_at < next_day)
        except ValueError:
            pass # Handle invalid date format gracefully

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

    # Handle nested view
    is_nested = request.args.get('nested', 'false').lower() == 'true'
    if is_nested:
        query = query.filter(Note.parent_id.is_(None))

    # 2. Sorting
    sort_by = request.args.get('sort_by', 'id')
    order = request.args.get('order', 'asc')
    
    if hasattr(Note, sort_by):
        column = getattr(Note, sort_by)
        if order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    notes = query.all()

    return jsonify([serialize_note(n, nested=is_nested) for n in notes])

@notes_blueprint.route('/api/categories', methods=['GET']) 
def get_all_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name
    } for c in categories])

@notes_blueprint.route('/api/tags', methods=['GET'])
def get_all_tags():
    tags = Tag.query.all()
    return jsonify([{'id': t.id, 'name': t.name} for t in tags])

@notes_blueprint.route('/api/notes', methods=['POST'])
def create_note():
    data = request.json
    now = datetime.now()

    priority = data.get('priority', 'Medium')
    sub_data = data.get('subtasks', [])

    calculated_deadline = None
    if not sub_data:
        days = get_days_by_priority(priority)
        calculated_deadline = now + timedelta(days=days)
    else:
        total_days = 0
        for sub in sub_data:
            total_days += get_days_by_priority(sub.get('priority', 'Medium'))
        calculated_deadline = now + timedelta(days=total_days)


    """ deadline = None
    if data.get('deadline'):
        try:
            deadline = datetime.fromisoformat(data['deadline'])
        except ValueError:
            pass """

    new_note = Note(
        title = data.get('title'),
        description = data.get('description'),
        priority = priority,
        is_done = data.get('is_done', False),
        deadline = calculated_deadline,
        category_id = data.get('category_id'),
        parent_id = data.get('parent_id'),
        recurrence_rule = data.get('recurrence_rule')
    )
    db.session.add(new_note)
    db.session.flush()

    subtasks_data = data.get('subtasks', [])
    if isinstance(subtasks_data, list):
        for subtask in subtasks_data:
            sub_priority = subtask.get('priority', 'Medium')
            sub_days = get_days_by_priority(sub_priority)
            subtask = Note(
                title=subtask.get('title'),
                description=subtask.get('description'),
                priority=sub_priority,
                deadline=now + timedelta(days=sub_days),
                parent_id=new_note.id
            )
            db.session.add(subtask)
    db.session.commit()

    return jsonify({'message': 'Note created successfully', 'deadline': calculated_deadline.isoformat()}), 201
        

    # Handle tags
    if 'tags' in data and isinstance(data['tags'], list):
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            new_note.tags.append(tag)

    # Calculate next occurrence if rule exists
    if new_note.recurrence_rule and new_note.deadline:
        try:
            rule = rrulestr(new_note.recurrence_rule, dtstart=new_note.deadline)
            new_note.next_occurrence_date = rule.after(new_note.deadline)
        except Exception:
            pass # Ignore invalid rules for now

    db.session.add(new_note)
    db.session.commit()

    return jsonify({'message': 'Note created successfully'}), 201

@notes_blueprint.route('/api/notes/<int:note_id>', methods=['GET','PUT'])
def update_or_get_note(note_id):
    note = Note.query.get_or_404(note_id)

    if request.method == 'GET':
        is_nested = request.args.get('nested', 'false').lower() == 'true'
        return jsonify(serialize_note(note, nested=is_nested))
    data = request.json

    note.title = data.get('title', note.title)
    note.description = data.get('description', note.description)
    note.priority = data.get('priority', note.priority)
    note.category_id = data.get('category_id', note.category_id)
    note.parent_id = data.get('parent_id', note.parent_id)
    note.recurrence_rule = data.get('recurrence_rule', note.recurrence_rule)
    
    if 'is_done' in data:
        if data['is_done']:
            # Check if any direct subtask is incomplete
            if any(not sub.is_done for sub in note.subtasks):
                return jsonify({'error': 'Cannot complete task. All subtasks must be completed first.'}), 400
        
        # Handle Recurrence: If completing, create the next task
        if data['is_done'] and not note.is_done and note.recurrence_rule:
            try:
                # Calculate next deadline based on rule
                start_date = note.deadline or datetime.now()
                rule = rrulestr(note.recurrence_rule, dtstart=start_date)
                next_date = rule.after(datetime.now())
                
                if next_date:
                    new_note = Note(
                        title=note.title,
                        description=note.description,
                        priority=note.priority,
                        category_id=note.category_id,
                        parent_id=note.parent_id, # Keep hierarchy?
                        deadline=next_date,
                        recurrence_rule=note.recurrence_rule,
                        next_occurrence_date=rule.after(next_date)
                    )
                    # Copy tags
                    for tag in note.tags:
                        new_note.tags.append(tag)
                    
                    db.session.add(new_note)
            except Exception as e:
                print(f"Failed to generate recurring task: {e}")

        note.is_done = data['is_done']

        # Handle tags
        if 'tags' in data:
            note.tags.clear() # Simple approach: clear and re-add
            if isinstance(data['tags'], list):
                for tag_name in data['tags']:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    note.tags.append(tag)
        # Update parent status if all subtasks are done
        curr = note
        while curr.parent_id:
            parent = curr.parent
            if not parent:
                break
            
            all_done = all(sub.is_done for sub in parent.subtasks)
            parent.is_done = all_done
            curr = parent

    if note.parent_id == note.id:
        return jsonify({'error': 'A task cannot be its own subtask'}), 400

    if 'parent_id' in data:
        new_parent_id = data.get('parent_id')

        if new_parent_id == note.id:
            return jsonify({'error': 'A task cannot be its own subtask'}), 400

        if new_parent_id is not None:
            parent_task = Note.query.get(new_parent_id)
            if parent_task and parent_task.parent_id is not None:
                return jsonify({'error': 'Subtasks can not have their own subtasks'}), 400
    
    if 'deadline' in data:
        if data['deadline']:
            try:
                note.deadline = datetime.fromisoformat(data['deadline'])
            except ValueError:
                pass
        else:
            note.deadline = None

    # Recalculate next occurrence if deadline or rule changed
    if (data.get('recurrence_rule') or 'deadline' in data) and note.recurrence_rule and note.deadline:
        try:
            rule = rrulestr(note.recurrence_rule, dtstart=note.deadline)
            note.next_occurrence_date = rule.after(note.deadline)
        except Exception:
            pass

    db.session.commit()
    return {'message': 'Task updated successfully'}, 200

@notes_blueprint.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)

    Note.query.filter_by(parent_id=note_id).all()

    db.session.delete(note)
    db.session.commit()
    return jsonify({'message': 'Note  and it subtasks deleted'})

def get_days_by_priority(priority_name):
    mapping = {
        'Low': 15,
        'Medium': 10,
        'High': 5
    
    }
    return mapping.get(priority_name, 10)


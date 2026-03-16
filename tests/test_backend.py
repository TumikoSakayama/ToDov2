from datetime import datetime, timedelta
from models import Note

def test_root_route(client):
    """Test the API root route works."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Todo App Backend is Running" in response.data

def test_create_category_and_note(client):
    """Test creating a category and a note associated with it."""
    # 1. Create Category
    client.post('/api/categories', json={'name': 'Work'})
    
    # 2. Create Note
    note_data = {
        'title': 'Test Task',
        'description': 'Description',
        'priority': 1,
        'category_id': 1,
        'tags': ['urgent', 'backend']
    }
    response = client.post('/api/notes', json=note_data)
    assert response.status_code == 201

    # 3. Verify Note
    response = client.get('/api/notes')
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['title'] == 'Test Task'
    assert 'urgent' in data[0]['tags']

def test_subtask_completion_logic(client):
    """Test that you cannot complete a parent task if subtasks are pending."""
    # Create Parent
    client.post('/api/notes', json={'title': 'Parent Task'})
    
    # Create Child (Subtask)
    client.post('/api/notes', json={'title': 'Child Task', 'parent_id': 1})

    # Attempt to complete Parent (Should Fail)
    response = client.put('/api/notes/1', json={'is_done': True})
    assert response.status_code == 400
    assert b"All subtasks must be completed first" in response.data

    # Complete Child
    client.put('/api/notes/2', json={'is_done': True})

    # Attempt to complete Parent (Should Succeed)
    response = client.put('/api/notes/1', json={'is_done': True})
    assert response.status_code == 200

def test_recurrence_on_completion(client):
    """Test that completing a recurring task generates the next one."""
    today = datetime.now()
    
    # Create recurring task (Daily)
    note_data = {
        'title': 'Daily Standup',
        'recurrence_rule': 'FREQ=DAILY',
        'deadline': today.isoformat()
    }
    client.post('/api/notes', json=note_data)

    # Complete the task
    client.put('/api/notes/1', json={'is_done': True})

    # Check if a new task was created
    response = client.get('/api/notes')
    notes = response.get_json()
    
    assert len(notes) == 2
    # The first one should be done
    assert notes[0]['is_done'] is True
    # The second one should be open and have a deadline in the future
    assert notes[1]['is_done'] is False
    assert notes[1]['title'] == 'Daily Standup'

    # Verify new deadline is tomorrow
    # (Simple check: deadline string should not be equal)
    assert notes[0]['deadline'] != notes[1]['deadline']

def test_digest_recurring_command(app):
    """Test the CLI command for strict scheduling."""
    runner = app.test_cli_runner()
    
    with app.app_context():
        # Create a task that was due "yesterday" with a recurrence rule
        yesterday = datetime.now() - timedelta(days=1)
        note = Note(title="Old Recurring", recurrence_rule="FREQ=DAILY", 
                    deadline=yesterday, next_occurrence_date=yesterday)
        from models import db
        db.session.add(note)
        db.session.commit()

        # Run the CLI command
        result = runner.invoke(args=['digest-recurring'])
        assert "Recurring tasks processed" in result.output
        
        # Verify a new task was created even though we didn't complete the old one
        assert Note.query.count() == 2

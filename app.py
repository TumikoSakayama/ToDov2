from flask import Flask
from models import db, Note
from routes import notes_blueprint
from flask_migrate import Migrate
from datetime import datetime
from dateutil.rrule import rrulestr

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()  # Ensure tables are created
        print("Database tables created successfully!")

    app.register_blueprint(notes_blueprint)

    @app.cli.command("digest-recurring")
    def digest_recurring():
        """Check for recurring tasks due today and generate new ones."""
        now = datetime.now()
        # Find tasks that have a next occurrence date in the past/today and are not done yet
        # This is for 'strict' scheduling where tasks appear regardless of completion
        notes = Note.query.filter(Note.next_occurrence_date <= now).all()
        
        for note in notes:
            print(f"Processing recurring note: {note.title}")
            
            # 1. Create the new task instance for the due date
            new_task = Note(
                title=note.title,
                description=note.description,
                priority=note.priority,
                category_id=note.category_id,
                deadline=note.next_occurrence_date,
                recurrence_rule=note.recurrence_rule, 
                # We assume the new task continues the chain
            )
            db.session.add(new_task)

            # 2. Update the source task's next occurrence so we don't generate it again tomorrow
            rule = rrulestr(note.recurrence_rule, dtstart=note.next_occurrence_date)
            note.next_occurrence_date = rule.after(datetime.now())
        
        db.session.commit()
        print("Recurring tasks processed.")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
import flet as ft
import requests
from datetime import datetime, timedelta

API_URL = "http://127.0.0.1:5000/api/notes"

def main(page: ft.Page):
    current_task_payload = {}

    page.title = "My Advanced Todo App"
    page.theme_mode = "light" 
    page.window_width = 400
    page.window_height = 600
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER

    #UI_ELEMENTS
    tasks_view = ft.Column(spacing=10, scroll="adaptive")
    
    main_title = ft.TextField(label="Task Title", autofocus=True)
    main_desc = ft.TextField(label="Task Description", multiline=True)
    main_cat = ft.Dropdown(label="Category", value="Personal", options=[
        ft.dropdown.Option("Personal"), ft.dropdown.Option("Work"),
        ft.dropdown.Option("Health"), ft.dropdown.Option("Shopping"),
        ft.dropdown.Option("Finance"), ft.dropdown.Option("Home"),
        ft.dropdown.Option("Other")
    ])
    main_priority = ft.Dropdown(label="Priority", value="Low", options=[
        ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")
    ])

    sub_title = ft.TextField(label="Subtask Title")
    sub_desc = ft.TextField(label="Subtask Description", multiline=True)
    sub_priority = ft.Dropdown(label="Priority", value="Low", options=[
        ft.dropdown.Option("Low"), ft.dropdown.Option("Medium"), ft.dropdown.Option("High")
    ])

    sorting = ft.Dropdown(
        label="Sort By",
        value="deadline",
        width=120,
        options=[
            ft.dropdown.Option("deadline", "Deadline"),
            ft.dropdown.Option("priority", "Priority"),
            ft.dropdown.Option("category", "Category"),
            ft.dropdown.Option("status", "Status")
        ]
    )

    is_ascending = [True]

    # SUPPORT FUNCTIONS 
    def update_task(task_id, status):
        try:
            requests.put(f"{API_URL}/{task_id}", json={'is_done': status}, timeout=5)
            load_tasks()
        except Exception as ex:
            print(f"Update Error: {ex}")

    def build_task_ui(note):
        is_task_done = note.get('is_done', False)
        subtasks = note.get('subtasks', [])
        tid = note['id']
        title = note.get('title', "Untitled Task")

        is_overdue = False
        if note.get('deadline'):
            try:
                deadline_date = datetime.fromisoformat(note['deadline'])
                if deadline_date < datetime.now():
                    is_overdue = True
            except: pass

        should_be_disabled = is_task_done and is_overdue
        cb = ft.Checkbox(value=is_task_done, disabled=should_be_disabled)

        def on_change_cb(e):
            if cb.value: confirm_completion(tid, title, cb)
            else: update_task(tid, False)
        cb.on_change = on_change_cb

        # TEXT STYLES
        text_style = ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH if is_task_done else None)
        
        deadline_chip = ft.Container()
        if note.get('deadline'):
            try:
                date_obj = datetime.fromisoformat(note['deadline'])
                diff = (date_obj - datetime.now()).days
                color = ft.Colors.RED_ACCENT_700 if diff < 0 else ft.Colors.ORANGE_ACCENT_800 if diff <= 2 else ft.Colors.GREY_700
                deadline_chip = ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_MONTH, color=color, size=14),
                    ft.Text(date_obj.strftime('%b %d'), size=12, color=color, weight="bold")
                ], spacing=5)
            except: pass

        return ft.Card(
            content=ft.ListTile(
                leading=cb,
                title=ft.Text(title, weight="bold", style=text_style),
                subtitle=ft.Column([
                    ft.Text(f"Priority: {note.get('priority', 0)} | {note.get('category', 'Other')}"),
                    deadline_chip
                ], spacing=2),
                trailing=ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda _: (requests.delete(f"{API_URL}/{tid}"), load_tasks()))
            )
        )

    def load_tasks():
        try:
            response = requests.get(f"{API_URL}?nested=true", timeout=5)
            if response.status_code == 200:
                notes = response.json()
                tasks_view.controls.clear()
            
                def sort_key(n):
                    crit = sorting.value
                    if crit == "deadline": return n.get('deadline') or '9999-12-31'
                    if crit == "priority":
                        p = n.get('priority', 0)
                        if isinstance(p, str):
                            mapping = {"Low": 0, "Medium": 1, "High": 2}
                        return mapping.get(p, 0)
                    return p if p is not None else 0
                    if crit == "category": return (n.get('category') or 'Z').lower()
                    if crit == "status": return 1 if n.get('is_done') else 0
                    return 0

                # Corrección de la lógica de ordenamiento
                notes.sort(key=sort_key, reverse=not is_ascending[0])

                for note in notes:
                    if note.get('parent_id') is None:
                        tasks_view.controls.append(build_task_ui(note))
                
                if not notes:
                    tasks_view.controls.append(ft.Text("No tasks found.", color="grey"))
                
                page.update()
        except Exception as ex:
            print(f"Error loading tasks: {ex}")

    def toggle_direction(e):
        is_ascending[0] = not is_ascending[0] # Corregido: Acceso al índice [0]
        e.control.icon = ft.Icons.ARROW_UPWARD if is_ascending[0] else ft.Icons.ARROW_DOWNWARD
        load_tasks()

    dir_btn = ft.IconButton(icon=ft.Icons.ARROW_UPWARD, on_click=toggle_direction)
    sorting.on_change = lambda _: load_tasks()

    header = ft.Row(
        controls=[ft.Text("My Tasks", size=24, weight="bold"), ft.Row([sorting, dir_btn], spacing=0)],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    #DIALOGS
    def close_all_dialogs():
        add_task_dialog.open = False
        prompt_subtask_dialog.open = False
        subtask_form_dialog.open = False
        page.update()

    def finalize_and_send(e=None):
        try:
            requests.post(API_URL, json=current_task_payload, timeout=5)
            load_tasks()
            current_task_payload.clear()
        except Exception as ex: print(f"Save Error: {ex}")
        finally: close_all_dialogs()

    add_task_dialog = ft.AlertDialog(
        title=ft.Text("Add Task"),
        content=ft.Column([main_title, main_desc, main_cat, main_priority], tight=True),
        actions=[ft.TextButton("Save", on_click=lambda _: (current_task_payload.update({
            "title": main_title.value, "description": main_desc.value, "category": main_cat.value, 
            "priority": main_priority.value, "subtasks": []
        }), finalize_and_send()))]
    )

    #VALIDATION
    def confirm_completion(tid, title, cb_ref):
        def handle_yes(e):
            update_task(tid, True)
            confirm_dialog.open = False
            page.update()

        confirm_dialog = ft.AlertDialog(
            title=ft.Text("Confirm"),
            content=ft.Text(f"Mark {title} as done?"),
            actions=[
                ft.TextButton("No", on_click=lambda _: (setattr(cb_ref, "value", False), page.update(), setattr(confirm_dialog, "open", False))),
                ft.Button("Yes", on_click=handle_yes, bgcolor="green", color="white")
            ]
        )
        page.overlay.append(confirm_dialog)
        confirm_dialog.open = True
        page.update()

    #FINAL ASSEMBLY
    page.overlay.append(add_task_dialog)
    page.floating_action_button = ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=lambda _: (setattr(add_task_dialog, "open", True), page.update()))

    page.add(header, ft.Divider(), tasks_view)

    load_tasks()

if __name__ == "__main__":
    ft.run(main)